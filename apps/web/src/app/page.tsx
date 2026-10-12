import { disclaimers, landing } from "@/copy";

export default function Home() {
  return (
    <main>
      <h1>{landing.title}</h1>
      <p>{landing.tagline}</p>
      <ul>
        <li>{disclaimers.generated}</li>
        <li>{disclaimers.outside}</li>
        <li>{disclaimers.simulated}</li>
      </ul>
    </main>
  );
}
