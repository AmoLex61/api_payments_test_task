.mode csv
.import recon_our_records.csv our_records
.import recon_partner_statement.csv partner_statement

-- 1. Duplicate refs
SELECT ref, COUNT(*) AS row_count
FROM partner_statement
GROUP BY ref
HAVING COUNT(*) > 1;

-- Remove identical variants so duplicates do not multiply JOIN results.
CREATE TEMP VIEW partner_variants AS
SELECT DISTINCT ref, amount, currency, status
FROM partner_statement;

-- 2. Only in our records
SELECT o.ref, o.amount AS our_amount, o.currency, o.status AS our_status
FROM our_records AS o
LEFT JOIN partner_variants AS p ON p.ref = o.ref
WHERE p.ref IS NULL;

-- 3. Only in partner statement
SELECT p.ref, p.amount AS partner_amount, p.currency,
       p.status AS partner_status
FROM partner_variants AS p
LEFT JOIN our_records AS o ON o.ref = p.ref
WHERE o.ref IS NULL;

-- 4. Amount mismatch
SELECT o.ref, o.amount AS our_amount, p.amount AS partner_amount
FROM our_records AS o
INNER JOIN partner_variants AS p ON p.ref = o.ref
WHERE o.amount IS NOT p.amount;

-- 5. Status mismatch
SELECT o.ref, o.status AS our_status, p.status AS partner_status
FROM our_records AS o
INNER JOIN partner_variants AS p ON p.ref = o.ref
WHERE o.status IS NOT p.status;
