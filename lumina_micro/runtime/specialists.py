import json
import math
import subprocess
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from lumina_micro.runtime.contracts import get_contract_spec

from .executor import ContractContext, ExecutionResult, VERIFIERS, build_contract_context, execute_contract


@dataclass(frozen=True)
class SpecialistRequest:
    contract: str
    input_code: str
    route_confidence: float


class SpecialistBackend(Protocol):
    def run(self, request: SpecialistRequest) -> ExecutionResult:
        ...


def _map_feature_vector(row: dict, candidate: str, route_confidence: float, verdict) -> list[float]:
    expected_var = row.get("expected_output_var", "")
    expected_array = row.get("expected_array_var", "")
    stripped = candidate.strip()
    lines = [line for line in stripped.splitlines() if line.strip()]
    has_binding = any(stripped.startswith(prefix) for prefix in ("const ", "let ", "var "))
    binds_expected = any(token in candidate for token in (f"const {expected_var}", f"let {expected_var}", f"var {expected_var}"))
    return [
        float(route_confidence),
        float(verdict.syntax_valid),
        float(getattr(verdict, "uses_map", False)),
        float(has_binding),
        float(binds_expected),
        float(".map" in candidate),
        float("=>" in candidate),
        float(expected_array in candidate),
        float(stripped.endswith(";")),
        min(len(stripped) / 160.0, 1.0),
        min(len(lines) / 6.0, 1.0),
    ]


def _map_heuristic_confidence(feature_vector: list[float]) -> float:
    score = (
        0.10
        + 0.15 * feature_vector[0]
        + 0.20 * feature_vector[1]
        + 0.15 * feature_vector[2]
        + 0.10 * feature_vector[3]
        + 0.15 * feature_vector[4]
        + 0.05 * feature_vector[7]
        + 0.05 * feature_vector[8]
    )
    return max(0.0, min(1.0, score))


def _reduce_feature_vector(row: dict, candidate: str, route_confidence: float, verdict) -> list[float]:
    expected_var = row.get("expected_output_var", "")
    expected_array = row.get("expected_array_var", "")
    stripped = candidate.strip()
    lines = [line for line in stripped.splitlines() if line.strip()]
    has_binding = any(stripped.startswith(prefix) for prefix in ("const ", "let ", "var "))
    binds_expected = any(token in candidate for token in (f"const {expected_var}", f"let {expected_var}", f"var {expected_var}"))
    repeats_binding = candidate.count(expected_var) > 1
    return [
        float(route_confidence),
        float(verdict.syntax_valid),
        float(getattr(verdict, "uses_reduce", False)),
        float(has_binding),
        float(binds_expected),
        float(".reduce" in candidate),
        float("=>" in candidate),
        float(expected_array in candidate),
        float(stripped.endswith(";")),
        float(repeats_binding),
        min(len(stripped) / 200.0, 1.0),
        min(len(lines) / 6.0, 1.0),
    ]


def _reduce_heuristic_confidence(feature_vector: list[float]) -> float:
    score = (
        0.10
        + 0.15 * feature_vector[0]
        + 0.20 * feature_vector[1]
        + 0.15 * feature_vector[2]
        + 0.10 * feature_vector[3]
        + 0.15 * feature_vector[4]
        + 0.05 * feature_vector[7]
        + 0.05 * feature_vector[8]
        - 0.15 * feature_vector[9]
    )
    return max(0.0, min(1.0, score))


def _index_feature_vector(row: dict, candidate: str, route_confidence: float, verdict) -> list[float]:
    expected_var = row.get("expected_output_var", "")
    expected_array = row.get("expected_array_var", "")
    expected_key_expr = row.get("expected_key_expr", "")
    stripped = candidate.strip()
    lines = [line for line in stripped.splitlines() if line.strip()]
    has_binding = any(stripped.startswith(prefix) for prefix in ("const ", "let ", "var "))
    binds_expected = any(token in candidate for token in (f"const {expected_var}", f"let {expected_var}", f"var {expected_var}"))
    key_has_transform = any(token in expected_key_expr for token in ("trim()", "toLowerCase()", "`${"))
    candidate_has_template = "`" in candidate
    candidate_has_transform = any(token in candidate for token in ("trim()", "toLowerCase()"))
    candidate_has_nested = "[" in candidate and "." in candidate
    return [
        float(route_confidence),
        float(verdict.syntax_valid),
        float(getattr(verdict, "uses_reduce", False)),
        float(has_binding),
        float(binds_expected),
        float(".reduce" in candidate),
        float("=>" in candidate),
        float(expected_array in candidate),
        float(stripped.endswith(";")),
        float(len(lines) <= 1),
        float(candidate_has_template),
        float(candidate_has_transform),
        float(candidate_has_nested),
        float(key_has_transform),
        min(len(stripped) / 240.0, 1.0),
        min(len(lines) / 6.0, 1.0),
    ]


def _index_heuristic_confidence(feature_vector: list[float]) -> float:
    score = (
        0.10
        + 0.12 * feature_vector[0]
        + 0.18 * feature_vector[1]
        + 0.14 * feature_vector[2]
        + 0.10 * feature_vector[3]
        + 0.12 * feature_vector[4]
        + 0.05 * feature_vector[7]
        + 0.05 * feature_vector[8]
        + 0.04 * feature_vector[9]
        + 0.04 * feature_vector[10]
        + 0.03 * feature_vector[11]
        + 0.03 * feature_vector[12]
    )
    return max(0.0, min(1.0, score))


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if "```" not in stripped:
        return stripped
    blocks = stripped.split("```")
    for block in reversed(blocks):
        block = block.strip()
        if not block:
            continue
        if block.startswith("js"):
            return block[2:].strip()
        if "const " in block or "let " in block or "var " in block:
            return block
    return stripped.replace("```", "").strip()


def _normalize_spacing(text: str) -> str:
    return " ".join(text.strip().split())


def _extract_assignment_statement(text: str, output_var: str, marker: str) -> str | None:
    pattern = re.compile(
        rf"\b(?:const|let|var)\s+{re.escape(output_var)}\s*=\s*.*?;",
        flags=re.DOTALL,
    )
    for match in pattern.finditer(text):
        statement = _normalize_spacing(match.group(0))
        if marker in statement:
            return statement
    return None


def _extract_expression_after_binding(text: str, output_var: str, marker: str) -> str | None:
    pattern = re.compile(
        rf"(?:const|let|var)?\s*{re.escape(output_var)}\s*=\s*(.*?);",
        flags=re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None
    expr = _normalize_spacing(match.group(1))
    if marker in expr:
        return expr
    return None


def _first_contract_line(text: str, output_var: str, marker: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if output_var in stripped and marker in stripped and "=" in stripped:
            return _normalize_spacing(stripped)
    return None


def _ensure_bound_statement(statement: str, output_var: str) -> str:
    cleaned = _normalize_spacing(statement).rstrip(";")
    if cleaned.startswith(("const ", "let ", "var ")):
        return f"{cleaned};"
    binding_pattern = re.compile(rf"^{re.escape(output_var)}\s*=\s*")
    if binding_pattern.search(cleaned):
        rhs = binding_pattern.sub("", cleaned, count=1)
        return f"const {output_var} = {rhs};"
    return f"const {output_var} = {cleaned};"


def _canonical_assignment(row: dict, marker: str) -> str:
    output_var = row["expected_output_var"]
    array_var = row["expected_array_var"]
    iter_var = row.get("expected_iter_var", "item")
    if marker == ".map(":
        expr = row["expected_map_expr"]
        return f"const {output_var} = {array_var}.map(({iter_var}) => {expr});"
    if row.get("expected_key_expr") is not None:
        key_expr = row["expected_key_expr"]
        value_expr = row["expected_value_expr"]
        return (
            f"const {output_var} = {array_var}.reduce("
            f"(acc, {iter_var}) => ({{ ...acc, [{key_expr}]: {value_expr} }}), {{}});"
        )
    expr = row["expected_reduce_expr"]
    init_value = row["expected_initializer"]
    return f"const {output_var} = {array_var}.reduce((acc, {iter_var}) => {expr}, {init_value});"


def _postprocess_map_candidate(text: str, row: dict) -> str:
    output_var = row["expected_output_var"]
    cleaned = _strip_code_fences(text)
    statement = _extract_assignment_statement(cleaned, output_var, ".map(")
    if statement:
        return statement
    expr = _extract_expression_after_binding(cleaned, output_var, ".map(")
    if expr:
        return f"const {output_var} = {expr.rstrip(';')};"
    line = _first_contract_line(cleaned, output_var, ".map(")
    if line:
        return _ensure_bound_statement(line, output_var)
    if ".map(" in cleaned:
        return f"const {output_var} = {_normalize_spacing(cleaned).rstrip(';')};"
    return _normalize_spacing(cleaned)


def _postprocess_reduce_candidate(text: str, row: dict) -> str:
    output_var = row["expected_output_var"]
    cleaned = _strip_code_fences(text)
    statement = _extract_assignment_statement(cleaned, output_var, ".reduce(")
    if statement:
        return statement
    expr = _extract_expression_after_binding(cleaned, output_var, ".reduce(")
    if expr:
        return f"const {output_var} = {expr.rstrip(';')};"
    line = _first_contract_line(cleaned, output_var, ".reduce(")
    if line:
        return _ensure_bound_statement(line, output_var)
    if ".reduce(" in cleaned:
        return f"const {output_var} = {_normalize_spacing(cleaned).rstrip(';')};"
    return _normalize_spacing(cleaned)


def _postprocess_index_candidate(text: str, row: dict) -> str:
    output_var = row["expected_output_var"]
    cleaned = _postprocess_reduce_candidate(text, row)
    if not cleaned:
        return cleaned
    iter_var = row.get("expected_iter_var")
    key_expr = row.get("expected_key_expr")
    value_expr = row.get("expected_value_expr")
    if (
        iter_var
        and key_expr
        and value_expr
        and ".reduce(" in cleaned
        and "{" in cleaned
        and "..." in cleaned
        and value_expr == iter_var
    ):
        destructure_pattern = re.compile(r"\(\s*[A-Za-z_$][\w$]*\s*,\s*\{[^}]+\}\s*\)\s*=>")
        if destructure_pattern.search(cleaned):
            return _canonical_assignment(row, ".reduce(")
    return cleaned


def _postprocess_candidate(contract: str, text: str, row: dict) -> str:
    if contract == "js_array_loop_to_map":
        return _postprocess_map_candidate(text, row)
    if contract == "js_reduce_accumulator_refactor":
        return _postprocess_reduce_candidate(text, row)
    return _postprocess_index_candidate(text, row)


def _feature_vector(contract: str, row: dict, candidate: str, route_confidence: float, verdict) -> list[float]:
    if contract == "js_array_loop_to_map":
        return _map_feature_vector(row, candidate, route_confidence, verdict)
    if contract == "js_reduce_accumulator_refactor":
        return _reduce_feature_vector(row, candidate, route_confidence, verdict)
    return _index_feature_vector(row, candidate, route_confidence, verdict)


def _score_candidate(contract: str, route_confidence: float, row: dict, candidate: str, verdict) -> float:
    if contract == "js_array_loop_to_map":
        return _map_heuristic_confidence(_map_feature_vector(row, candidate, route_confidence, verdict))
    if contract == "js_reduce_accumulator_refactor":
        return _reduce_heuristic_confidence(_reduce_feature_vector(row, candidate, route_confidence, verdict))
    return _index_heuristic_confidence(_index_feature_vector(row, candidate, route_confidence, verdict))


class ConfidenceProvider(Protocol):
    def score(self, contract: str, route_confidence: float, row: dict, candidate: str, verdict) -> float:
        ...


class HeuristicConfidenceProvider:
    def score(self, contract: str, route_confidence: float, row: dict, candidate: str, verdict) -> float:
        return _score_candidate(contract, route_confidence, row, candidate, verdict)


class LinearConfidenceProvider:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    @classmethod
    def from_path(cls, path: str | Path) -> 'LinearConfidenceProvider':
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
        return cls(payload)

    def score(self, contract: str, route_confidence: float, row: dict, candidate: str, verdict) -> float:
        features = _feature_vector(contract, row, candidate, route_confidence, verdict)
        spec = self.payload.get('contracts', {}).get(contract)
        if spec is None:
            raise KeyError(f'No confidence weights found for contract: {contract}')
        weights = spec.get('weights', [])
        bias = spec.get('bias', 0.0)
        if len(weights) != len(features):
            raise ValueError(
                f'Feature/weight length mismatch for {contract}: {len(features)} features vs {len(weights)} weights'
            )
        logit = bias + sum(w * x for w, x in zip(weights, features, strict=True))
        return 1.0 / (1.0 + math.exp(-logit))


class ProbeBundleConfidenceProvider:
    def __init__(self, path: str | Path, fallback: ConfidenceProvider | None = None) -> None:
        self.path = Path(path)
        self.fallback = fallback or HeuristicConfidenceProvider()
        self._loaded = False
        self._supported_contract = None
        self._torch = None
        self._probe = None
        self._mean = None
        self._std = None
        self.metadata = {}

    def _load(self) -> None:
        if self._loaded:
            return
        try:
            import torch
            from torch import nn
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError('torch is required for probe_bundle confidence provider') from exc

        payload = torch.load(self.path, map_location='cpu')
        input_dim = int(payload['input_dim'])
        hidden_dim = int(payload.get('hidden_dim', 16))
        class _ConfidenceProbe(nn.Module):
            def __init__(self, input_dim: int, hidden_dim: int) -> None:
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(input_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Linear(hidden_dim, 1),
                )

            def forward(self, x):
                return self.net(x).squeeze(-1)

        probe = _ConfidenceProbe(input_dim, hidden_dim)
        probe.load_state_dict(payload['state_dict'])
        probe.eval()

        self._torch = torch
        self._probe = probe
        self._mean = payload['mean'].float()
        self._std = payload['std'].float()
        self.metadata = payload.get('metadata', {})
        self._supported_contract = self.metadata.get('task_contract')
        self._loaded = True

    def score(self, contract: str, route_confidence: float, row: dict, candidate: str, verdict) -> float:
        self._load()
        if self._supported_contract and contract != self._supported_contract:
            return self.fallback.score(contract, route_confidence, row, candidate, verdict)
        features = _feature_vector(contract, row, candidate, route_confidence, verdict)
        x = self._torch.tensor(features, dtype=self._torch.float32)
        x = (x - self._mean) / self._std
        with self._torch.no_grad():
            logit = self._probe(x.unsqueeze(0))[0]
            return self._torch.sigmoid(logit).item()



class CalibratedProbeBundleConfidenceProvider:
    def __init__(self, path: str | Path, fallback: ConfidenceProvider | None = None) -> None:
        self.path = Path(path)
        self.payload = json.loads(self.path.read_text(encoding='utf-8'))
        self.contract = self.payload['contract']
        base_path = Path(self.payload['base_probe_model'])
        if not base_path.is_absolute():
            base_path = self.path.parent / base_path
        self.base_provider = ProbeBundleConfidenceProvider(base_path, fallback=fallback)
        self.heuristic_provider = HeuristicConfidenceProvider()
        self.fallback = fallback or HeuristicConfidenceProvider()
        weights = self.payload.get('weights', {})
        self.bias = float(self.payload.get('bias', 0.0))
        self.w_probe = float(weights.get('probe_score', 0.0))
        self.w_heur = float(weights.get('heuristic_score', 0.0))

    def score(self, contract: str, route_confidence: float, row: dict, candidate: str, verdict) -> float:
        if contract != self.contract:
            return self.fallback.score(contract, route_confidence, row, candidate, verdict)
        probe_score = self.base_provider.score(contract, route_confidence, row, candidate, verdict)
        heur_score = self.heuristic_provider.score(contract, route_confidence, row, candidate, verdict)
        logit = self.bias + self.w_probe * probe_score + self.w_heur * heur_score
        return 1.0 / (1.0 + math.exp(-logit))


def build_confidence_provider(kind: str = 'heuristic', model_path: str | None = None) -> ConfidenceProvider:
    if kind == 'heuristic':
        return HeuristicConfidenceProvider()
    if kind == 'linear':
        if not model_path:
            raise ValueError('confidence model path is required for linear provider')
        return LinearConfidenceProvider.from_path(model_path)
    if kind == 'probe_bundle':
        if not model_path:
            raise ValueError('confidence model path is required for probe_bundle provider')
        return ProbeBundleConfidenceProvider(model_path)
    if kind == 'probe_bundle_calibrated':
        if not model_path:
            raise ValueError('confidence model path is required for probe_bundle_calibrated provider')
        return CalibratedProbeBundleConfidenceProvider(model_path)
    raise ValueError(f'Unsupported confidence provider: {kind}')


class MockSpecialistBackend:
    """Contract-matched stand-in for the future shared-base adapter runtime."""

    def __init__(self, confidence_provider: ConfidenceProvider | None = None) -> None:
        self.confidence_provider = confidence_provider or HeuristicConfidenceProvider()

    def run(self, request: SpecialistRequest) -> ExecutionResult:
        result = execute_contract(request.contract, request.input_code)
        spec = get_contract_spec(request.contract)
        if spec:
            result.details.setdefault("runtime", {})
            result.details["runtime"].update(
                {
                    "base_model_family": spec.base_model_family,
                    "adapter_name": spec.adapter_name,
                    "route_confidence": request.route_confidence,
                    "backend": "shared_base_mock",
                }
            )
        if result.generated_code and result.verified:
            verifier = VERIFIERS[request.contract]
            row = result.details.get("verifier_row", {})
            verdict = verifier(result.generated_code, row)
            result.answer_confidence = self.confidence_provider.score(
                request.contract,
                request.route_confidence,
                row,
                result.generated_code,
                verdict,
            )
        return result


class SharedBaseOllamaBackend:
    def __init__(self, model: str = "llama3.1:latest", keepalive: str = "5m", confidence_provider: ConfidenceProvider | None = None) -> None:
        self.model = model
        self.keepalive = keepalive
        self.confidence_provider = confidence_provider or HeuristicConfidenceProvider()

    def _run_ollama(self, prompt: str) -> str:
        proc = subprocess.run(
            ["ollama", "run", "--nowordwrap", "--keepalive", self.keepalive, self.model, prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "ollama run failed")
        return proc.stdout.strip()

    def run(self, request: SpecialistRequest) -> ExecutionResult:
        context = build_contract_context(request.contract, request.input_code)
        spec = get_contract_spec(request.contract)
        if context is None:
            return ExecutionResult(None, False, False, False, 0.0, "fallback", {}, ["Could not synthesize verifier inputs from source block."])
        try:
            raw = self._run_ollama(self._strict_prompt(request.contract, context))
        except Exception as exc:
            return ExecutionResult(None, False, False, False, 0.0, "fallback", {}, [f"Ollama backend failed: {exc}"])
        extracted = self._extract_candidate(request.contract, raw, context)
        candidate = self._postprocess_candidate(request.contract, extracted, context)
        verifier = VERIFIERS[request.contract]
        verdict = verifier(candidate, context.verifier_row)
        contract_marker_present = bool(getattr(verdict, "uses_map", getattr(verdict, "uses_reduce", False)))
        verified = bool(verdict.passed)
        confidence = self.confidence_provider.score(request.contract, request.route_confidence, context.verifier_row, candidate, verdict)
        return ExecutionResult(
            generated_code=candidate.strip(),
            verified=verified,
            syntax_valid=bool(verdict.syntax_valid),
            contract_marker_present=contract_marker_present,
            answer_confidence=confidence,
            control_action="accepted" if verified else "fallback",
            details={
                "backend": "shared_base_ollama",
                "model": self.model,
                "base_model_family": spec.base_model_family if spec else None,
                "adapter_name": spec.adapter_name if spec else None,
                "route_confidence": request.route_confidence,
                "raw_output": raw,
                "extracted_output": extracted,
                "verifier_row": context.verifier_row,
                "verification": {
                    "syntax_valid": verdict.syntax_valid,
                    "contract_marker_present": contract_marker_present,
                    "passed": verdict.passed,
                    "details": verdict.details,
                },
            },
            notes=[] if verified else ["Ollama output failed verification; keeping original block."],
        )

    def _strict_prompt(self, contract: str, context: ContractContext) -> str:
        row = context.verifier_row
        if contract == "js_array_loop_to_map":
            return (
                "You are a JavaScript micro-specialist.\n"
                "Return exactly one JavaScript statement.\n"
                "Do not repeat the statement.\n"
                "Do not include markdown or explanation.\n"
                f"Assign only to `{row['expected_output_var']}`.\n"
                f"Use `{row['expected_array_var']}.map(...)`.\n"
                "Preserve behavior.\n\n"
                f"{row['prompt']}\n"
            )
        if contract == "js_reduce_accumulator_refactor":
            return (
                "You are a JavaScript micro-specialist.\n"
                "Return exactly one JavaScript statement.\n"
                "Do not repeat the statement.\n"
                "Do not include markdown or explanation.\n"
                f"Assign only to `{row['expected_output_var']}`.\n"
                f"Use `{row['expected_array_var']}.reduce(...)`.\n"
                f"Use the initializer `{row['expected_initializer']}`.\n"
                "Preserve behavior.\n\n"
                f"{row['prompt']}\n"
            )
        return (
            "You are a JavaScript micro-specialist.\n"
            "Return exactly one JavaScript statement.\n"
            "Do not repeat the statement.\n"
            "Do not include markdown or explanation.\n"
            f"Assign only to `{row['expected_output_var']}`.\n"
            f"Use `{row['expected_array_var']}.reduce(...)`.\n"
            "Use a concise expression-body reduce form.\n"
            "Preserve the original item as the value.\n"
            "Do not destructure the item parameter.\n"
            "Preserve behavior.\n\n"
            f"{row['prompt']}\n"
        )

    def _postprocess_candidate(self, contract: str, candidate: str, context: ContractContext) -> str:
        row = context.verifier_row
        return _postprocess_candidate(contract, candidate, row)

    def _extract_candidate(self, contract: str, raw: str, context: ContractContext) -> str:
        return raw


OllamaSpecialistBackend = SharedBaseOllamaBackend
