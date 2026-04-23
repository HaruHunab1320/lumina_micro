# Case Gallery

This gallery gives concrete accepted and rejected examples for the three frozen contracts.

The goal is not breadth. The goal is to make the verifier behavior legible.

## 1. `js_array_loop_to_map`

### Accepted

Input:

```js
const cleaned = [];
for (let i = 0; i < words.length; i++) {
  cleaned.push(words[i].trim());
}
```

Accepted rewrite:

```js
const cleaned = words.map((word) => word.trim());
```

Verifier outcome:

- syntax valid: `true`
- uses `.map`: `true`
- tests passed: `true`

### Rejected

Candidate:

```js
words.map((word) => word.trim());
```

Why rejected:

- syntax valid: `true`
- uses `.map`: `true`
- tests passed: `false`
- reason: missing expected output binding (`cleaned` is undefined in verifier execution)

## 2. `js_reduce_accumulator_refactor`

### Accepted

Input:

```js
let totalAge = 0;
for (const user of users) {
  totalAge += user.age;
}
```

Accepted rewrite:

```js
const totalAge = users.reduce((acc, user) => acc + user.age, 0);
```

Verifier outcome:

- syntax valid: `true`
- uses `.reduce`: `true`
- tests passed: `true`

### Rejected

Candidate:

```js
users.reduce((acc, user) => acc + user.age, 0);
```

Why rejected:

- syntax valid: `true`
- uses `.reduce`: `true`
- tests passed: `false`
- reason: missing expected output binding (`totalAge` is undefined in verifier execution)

## 3. `js_reduce_object_index_builder`

### Accepted

Input:

```js
const articlesByAuthorSlug = {};
for (const article of articles) {
  const key = `${article.author.handle.toLowerCase()}:${article.slug}`;
  articlesByAuthorSlug[key] = article;
}
```

Accepted rewrite:

```js
const articlesByAuthorSlug = articles.reduce(
  (acc, article) => ({ ...acc, [`${article.author.handle.toLowerCase()}:${article.slug}`]: article }),
  {}
);
```

Verifier outcome:

- syntax valid: `true`
- uses `.reduce`: `true`
- tests passed: `true`

### Rejected

Candidate:

```js
const articlesByAuthorSlug = articles.reduce(
  (acc, { author, slug, ...rest }) => ({ ...acc, [`${author.handle.toLowerCase()}:${slug}`]: rest }),
  {}
);
```

Why rejected:

- syntax valid: `true`
- uses `.reduce`: `true`
- tests passed: `false`
- reason: the contract requires preserving the original item as the value; this candidate drops fields and changes value semantics

## 4. `public_eval_v2` examples

These examples come from the current public comparison slice rather than the frozen historical runs.

### A. Prompt-only failure on accumulator reduce

Row: `acc_h`

Input:

```js
let teamKeyChars = 0;
for (const member of members) {
  teamKeyChars += `${member.team.slug}:${member.profile.handle.trim().toLowerCase()}`.length;
}
```

`builder_only` candidate:

```js
const teamKeyChars = members.reduce((acc, member) => acc + `${member.team.slug}:${member.profile.handle.trim().toLowerCase()}`.length, 0);
```

`prompt_only` candidate:

```js
const teamKeyChars = members.reduce((acc, member) => acc + (${member.team.slug}:${member.profile.handle.trim().toLowerCase()}).length, 0);
```

Observed behavior:

- `builder_only`: passes
- `prompt_only`: fails syntax
- `runtime_gated`: rejects the same prompt candidate and falls back

Why this matters:

- the failure is not semantic uncertainty
- it is a concrete syntax break introduced by the model in a templated-string expression
- the runtime does not repair it; it simply refuses to accept it

### B. Prompt-only failure on object-index reduce

Row: `idx_h`

Input:

```js
const invoicesByOwnerEmail = {};
for (const invoice of invoices) {
  invoicesByOwnerEmail[invoice.customer.account.owner.email.trim().toLowerCase()] = invoice;
}
```

`prompt_only` candidate:

```js
const invoicesByOwnerEmail = invoices.reduce((acc, invoice) => { acc[invoice.customer.account.owner.email.trim().toLowerCase()] = invoice;
```

Observed behavior:

- syntax valid: `false`
- required construct present: `true`
- verifier pass: `false`
- runtime action: fallback

Why this matters:

- the model is very close structurally
- but an incomplete block body is enough to make the rewrite unsafe
- verifier-backed rejection is doing real work here

## 5. What these examples show

The failure boundary is usually not "the model did something random."

It is more specific:

- omitted binding
- malformed template-string expression
- incomplete reduce block body
- subtle semantic drift while still looking structurally plausible

That is exactly why the verifier-backed contract is necessary. Textual plausibility is not enough.
