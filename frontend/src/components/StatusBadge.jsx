const STATUS_MAP = {
  manual_review:        { label: 'Manual Review',       cls: 'badge-manual' },
  checking_payment:     { label: 'Checking Payment',    cls: 'badge-checking' },
  payment_not_confirmed:{ label: 'Not Confirmed',       cls: 'badge-failed' },
  safe_to_release:      { label: 'Safe to Release',     cls: 'badge-safe' },
  released:             { label: 'Released',            cls: 'badge-released' },
}

export default function StatusBadge({ status }) {
  const s = STATUS_MAP[status] || { label: status, cls: 'badge-manual' }
  return <span className={s.cls}>{s.label}</span>
}
