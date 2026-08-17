import { HealthStatus } from "@/components/health-status";

const capabilities = [
  ["Investigate", "Correlate logs, metrics, deployments, and runbooks."],
  ["Explain", "Rank root-cause hypotheses with traceable evidence."],
  ["Control", "Require a reviewer before any sensitive remediation."],
];

export default function Home() {
  return (
    <main>
      <nav>
        <div className="brand"><span className="mark">S</span> SentinelAI</div>
        <HealthStatus />
      </nav>

      <section className="hero">
        <p className="eyebrow">AGENTIC INCIDENT RESPONSE</p>
        <h1>From alert to evidence-backed action.</h1>
        <p className="lede">
          A durable AI investigator that diagnoses production incidents and keeps humans in
          control of remediation.
        </p>
        <div className="actions">
          <button disabled>Launch investigation</button>
          <a href="http://localhost:8000/docs">Explore API</a>
        </div>
        <p className="day-one">Foundation online · Investigation workflows arrive on Day 4</p>
      </section>

      <section className="capabilities" aria-label="Platform capabilities">
        {capabilities.map(([title, description], index) => (
          <article key={title}>
            <span>0{index + 1}</span>
            <h2>{title}</h2>
            <p>{description}</p>
          </article>
        ))}
      </section>
    </main>
  );
}

