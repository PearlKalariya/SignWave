export interface Meeting {
  id: string;
  title: string;
  room_code: string;
  host_id: string;
  host_name: string;
  started_at: string;
  ended_at: string | null;
  participants: string[];
  is_active: boolean;
}

export interface TranscriptLine {
  id: string;
  speaker_id: string;
  speaker_name: string;
  text: string;
  source: "speech" | "sign";
  timestamp: string;
}

export interface RecognitionState {
  current_letter: string;
  current_word: string;
  sentence: string;
}

export interface RecognitionMessage {
  sign: string | null;
  confidence: number;
  state: RecognitionState;
}

export interface Summary {
  meeting_id: string;
  title: string;
  generated_at: string;
  decisions: string[];
  action_items: { task: string; owner?: string; deadline?: string }[];
  risks: string[];
  participants: string[];
  full_summary: string;
  raw_transcript: string;
}

export interface Participant {
  user_id: string;
  user_name: string;
}
