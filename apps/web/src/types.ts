export type Difficulty = "basic" | "medium" | "advanced";
export type Launch = {
  speed_m_s: number;
  angle_deg: number;
  height_m: number;
  gravity_m_s2: 10;
  air_resistance: false;
};
export type Control = {
  min: number;
  max: number;
  step?: number;
  editable: boolean;
};
export type Lab = {
  id: string;
  published: boolean;
  course: string;
  topic: string;
  title: string;
  difficulty: Difficulty;
  seed: number;
  instruction: string;
  target_m: number;
  tolerance_m: number;
  initial: Launch;
  controls: Record<"angle_deg" | "speed_m_s" | "height_m", Control>;
  rubric: Record<string, number>;
  max_score: number;
};
export type Attempt = { id: string; token: string; phase: string };
export type Report = {
  id: string;
  alias: string;
  phase: string;
  lab_id: string;
  run_count: number;
  penalized_runs: number;
  scores: Record<
    "procedure" | "comprehension" | "physical" | "efficiency",
    number | null
  >;
  total: number | null;
  max_score: number;
  passed: boolean | null;
  status: string;
  summary: string;
  result: null | {
    range_m: number;
    flight_time_s: number;
    max_height_m: number;
  };
  explanations: { text: string; received_at: string }[];
  evidence: SimEvent[];
  reviews: {
    procedure: number;
    comprehension: number;
    reason: string;
    reviewed_at: string;
  }[];
};
export type SimEvent = {
  id: string;
  kind:
    | "control"
    | "launch"
    | "landed"
    | "reset"
    | "erase"
    | "measurement"
    | "pause"
    | "invalidated";
  run_id?: string;
  state?: Launch;
  control?: string;
  value?: number | boolean | string;
  observed_range_m?: number;
  observed_time_s?: number;
};
