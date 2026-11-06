import { useEffect, useReducer } from "react";

import {
  debateReducer,
  initialDebateState,
  type DebateState,
} from "@/features/debate/utils/debateState";
import { type DebateEvent, EVENT_TYPES } from "@/types";
import { api } from "@/api";

export function useDebateStream(debateId: string | undefined): DebateState {
  const [state, dispatch] = useReducer(debateReducer, initialDebateState);

  useEffect(() => {
    if (!debateId) return;

    dispatch({ kind: "reset" });

    const source = new EventSource(api.eventsUrl(debateId));
    let finished = false;

    const onEvent = (message: MessageEvent<string>) => {
      const event = JSON.parse(message.data) as DebateEvent;
      dispatch({ kind: "event", id: Number(message.lastEventId), event });

      if (event.type === "debate_completed" || event.type === "debate_failed") {
        finished = true;
        source.close();
      }
    };

    for (const type of EVENT_TYPES) source.addEventListener(type, onEvent);

    source.onerror = () => {
      if (!finished && source.readyState === EventSource.CLOSED) {
        dispatch({ kind: "connection_lost" });
      }
    };

    return () => {
      finished = true;
      source.close();
    };
  }, [debateId]);

  return state;
}
