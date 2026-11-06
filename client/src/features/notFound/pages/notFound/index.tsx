import { ArrowLeft } from "lucide-react";
import { Link } from "react-router";

import { Styled } from "@/styled";

interface NotFoundPageProps {
  title?: string;
  detail?: string;
}

export function NotFoundPage({
  title = "Page not found",
  detail = "There's nothing at this address.",
}: NotFoundPageProps) {
  return (
    <div className="flex flex-col items-start gap-4 py-16">
      <p className="font-mono text-sm text-judge">404</p>
      <h1 className={Styled.DetailTitle}>{title}</h1>
      <p className="text-ink-muted">{detail}</p>

      <Link
        to="/"
        className="mt-2 inline-flex items-center gap-1.5 text-sm text-judge hover:underline"
      >
        <ArrowLeft className="size-4" aria-hidden />
        Back to CostCourt
      </Link>
    </div>
  );
}
