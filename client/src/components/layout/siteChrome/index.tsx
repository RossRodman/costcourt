import { Outlet, ScrollRestoration } from "react-router";

import { AmbientGlow } from "../ambientGlow";
import { Footer } from "../footer";
import { Header } from "../header";

export function SiteChrome() {
  return (
    <div className="relative flex min-h-dvh flex-col overflow-x-clip">
      <AmbientGlow />
      <Header />

      <main className="relative mx-auto w-full max-w-6xl flex-1 px-6 pt-12 pb-20">
        <Outlet />
      </main>

      <Footer />
      <ScrollRestoration />
    </div>
  );
}
