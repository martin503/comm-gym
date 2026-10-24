# Offer Judge Reliability

- judge: anthropic/claude-haiku-5.5 at temperature 0.0
- pairs attempted 120, unparseable verdicts 0 (0%)
- order consistency: 100% (threshold 75%)
- tie rate: 12%
- self-agreement: 100% on 5 re-judged pairs (threshold 80%)

| variant | pairs | mean judge win | verdict |
|---|---|---|---|
| template | 15 | 0.00 | LOSES/TIES |
| flattery | 15 | 0.00 | LOSES/TIES |
| keyword_stuffing | 15 | 0.00 | LOSES/TIES |
| padded_max_length | 15 | 0.00 | LOSES/TIES |
| emoji_spam | 15 | 0.00 | LOSES/TIES |
| injection_paraphrase | 15 | 0.00 | LOSES/TIES |
| wrong_personalization | 15 | 0.00 | LOSES/TIES |
| reference_self | 15 | 0.50 | ≈0.5 OK |

## Verdict: GO
