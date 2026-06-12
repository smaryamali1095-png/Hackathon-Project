export function MetricCard({ title, value, sub, tone = "" }) {
  return (
    <div className={`card metric ${tone}`}>
      <label>{title}</label>
      <h2>{value}</h2>
      <p>{sub}</p>
    </div>
  );
}

export function Badge({ children, tone = "" }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
