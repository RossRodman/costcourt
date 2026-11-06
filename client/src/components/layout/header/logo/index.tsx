import { Link } from "react-router";

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2.5 font-semibold tracking-tight">
      <img src="/favicon.svg" alt="" className="size-7" />
      CostCourt
    </Link>
  );
}
