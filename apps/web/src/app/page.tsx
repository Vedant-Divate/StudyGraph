import Link from "next/link";
import { disclaimers, landing } from "@/copy";
import { SiteShell } from "@/components/site-shell";

export default function Home() {
  return (
    <SiteShell active="home">
      <main>
        <section className="hero" aria-labelledby="welcome-title">
          <div className="hero-copy">
            <p className="eyebrow">A better way to study</p>
            <h1 id="welcome-title">
              StudyGraph
              <br />
              <em>makes ideas stick.</em>
            </h1>
            <p className="lede">{landing.tagline}</p>
            <div className="hero-actions">
              <Link className="button-primary" href="/courses">
                Explore your library <span aria-hidden="true">↗</span>
              </Link>
              <span className="muted">Built around what you’re learning.</span>
            </div>
          </div>
          <div className="hero-art" aria-label="A visual guide from sources to understanding">
            <div className="study-card">
              <div className="study-card-top">
                <span>Study, connected</span>
                <span aria-hidden="true">01 — 03</span>
              </div>
              <h2>Follow the thread</h2>
              <ol className="study-path">
                <li>
                  <span className="path-index">1</span>
                  <span>Start with your source material</span>
                </li>
                <li>
                  <span className="path-index">2</span>
                  <span>See how concepts connect</span>
                </li>
                <li>
                  <span className="path-index">3</span>
                  <span>Check what you understand</span>
                </li>
              </ol>
            </div>
          </div>
        </section>

        <section className="disclaimer-panel" aria-labelledby="grounded-title">
          <div>
            <p className="eyebrow">A note on AI</p>
            <h2 id="grounded-title">Stay curious. Check the source.</h2>
          </div>
          <ul className="disclaimer-list">
            <li>{disclaimers.generated}</li>
            <li>{disclaimers.outside}</li>
            <li>{disclaimers.simulated}</li>
          </ul>
        </section>
      </main>
    </SiteShell>
  );
}
