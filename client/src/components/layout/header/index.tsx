import { useHealth } from "@/hooks/useHealth";

import { Logo } from "./logo";
import { SourceLink } from "./sourceLink";
import { StatusPill } from "./statusPill";

export function Header() {
  const health = useHealth();

  return (
    <header className="relative mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-6 pt-6">
      <Logo />
      <nav className="flex items-center gap-3">
        <StatusPill state={health} />
        <SourceLink />
      </nav>
    </header>
  );
}
