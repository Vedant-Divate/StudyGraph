import Link from "next/link";
import { disclaimers, landing } from "@/copy";

export default function Home() {
  return (
    <main>
      <h1>{landing.title}</h1>
      <p>{landing.tagline}</p>
      <nav>
        <ul>
          <li>
            <Link href="/courses">Demo course library</Link>
          </li>
        </ul>
      </nav>
      <ul>
        <li>{disclaimers.generated}</li>
        <li>{disclaimers.outside}</li>
        <li>{disclaimers.simulated}</li>
      </ul>
    </main>
  );
}
