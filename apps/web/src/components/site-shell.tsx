import Link from "next/link";

export function SiteShell({
  children,
  active,
}: {
  children: React.ReactNode;
  active?: "home" | "library";
}) {
  return (
    <div className="site-shell">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <header className="site-header">
        <div className="site-header-inner">
          <Link className="brand" href="/" aria-label="StudyGraph home">
            <span className="brand-mark" aria-hidden="true">
              sg
            </span>
            StudyGraph
          </Link>
          <nav className="site-nav" aria-label="Main navigation">
            <Link href="/" aria-current={active === "home" ? "page" : undefined}>
              Home
            </Link>
            <Link
              href="/courses"
              aria-current={active === "library" ? "page" : undefined}
            >
              Library
            </Link>
          </nav>
          <Link className="header-action" href="/courses">
            Go to library <span aria-hidden="true">↗</span>
          </Link>
        </div>
      </header>
      <div className="site-content" id="main-content" tabIndex={-1}>
        {children}
      </div>
      <footer className="site-footer">
        <div className="site-footer-inner">
          <p>Study from your material. Follow the ideas back to their source.</p>
          <Link href="/courses">Browse the library</Link>
        </div>
      </footer>
    </div>
  );
}
