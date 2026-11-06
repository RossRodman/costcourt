import { QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { RouterProvider } from "react-router/dom";

import { createQueryClient } from "@/app/queryClient";
import { router as browserRouter } from "@/app/router";

type Router = typeof browserRouter;

interface AppProps {
  router?: Router;
}

export function App({ router = browserRouter }: AppProps) {
  const [queryClient] = useState(createQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
