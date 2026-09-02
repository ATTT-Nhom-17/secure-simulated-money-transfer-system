# Testing Checklist - Người 3

| ID | Test case | Expected result | Status |
|---|---|---|---|
| T01 | Register with valid data | Registration successful | ☐ |
| T02 | Register with mismatched passwords | Error shown | ☐ |
| T03 | Login with valid credentials | Dashboard opened | ☐ |
| T04 | Login with wrong password | Login rejected | ☐ |
| T05 | View account balance | Balance displayed | ☐ |
| T06 | Transfer valid amount | Transaction SUCCESS | ☐ |
| T07 | Transfer amount greater than balance | Transaction rejected | ☐ |
| T08 | Transfer to same account | Transaction rejected | ☐ |
| T09 | View transaction history | List displayed | ☐ |
| T10 | Open transaction detail | Security verification displayed | ☐ |
| T11 | Modify signed amount in a captured request | RSA verification should fail | ☐ |
| T12 | Replay the same request/nonce | Replay should be blocked | ☐ |
| T13 | Confirm encrypted balance is not stored as plaintext | AES ciphertext in DB | ☐ |
| T14 | Transfer with an invalid or missing PIN | Transaction rejected | ☐ |
