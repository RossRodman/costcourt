import { createBrowserRouter, type RouteObject } from "react-router";

import { SiteChrome } from "@/components/layout";
import { DebatePage, HomePage, NotFoundPage } from "@/features";

export const routes: RouteObject[] = [
  {
    element: <SiteChrome />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "debates/:debateId", element: <DebatePage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];

export const router = createBrowserRouter(routes);
