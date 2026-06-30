import { io, Socket } from "socket.io-client";
import { API_BASE } from "./api";

let socket: Socket | null = null;

// Single shared Socket.io connection to the meeting backend.
export function getSocket(): Socket {
  if (!socket) {
    socket = io(API_BASE, {
      transports: ["websocket"],
      autoConnect: true,
    });
  }
  return socket;
}

export interface SubtitlePayload {
  room_code: string;
  meeting_id: string;
  speaker_id: string;
  speaker_name: string;
  text: string;
  source: "speech" | "sign";
}

export function emitSubtitle(payload: SubtitlePayload): void {
  getSocket().emit("new_subtitle", payload);
}
