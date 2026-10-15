// DEMO DATA — illustrative only. Shown exclusively when the backend is not connected.
export const demoStats = { registered_users: 24, verifications: 128, genuine: 96, forged: 32 };

export const demoModels = [
  { kind: "cedar" as const, title: "CEDAR benchmark model", meta: "55 writers · writer_1.pkl", ready: true },
  { kind: "user" as const, title: "Maya Patel · maya", meta: "12 genuine references · maya.pkl", ready: true },
];

export const demoVerifications = [
  { id: 1, kind: "user" as const, target: "Maya Patel", prediction: "Genuine" as const, confidence: 0.94, created_at: "14:32" },
  { id: 2, kind: "cedar" as const, target: "CEDAR writer 12", prediction: "Forged" as const, confidence: 0.88, created_at: "13:58" },
  { id: 3, kind: "user" as const, target: "Rahul Iyer", prediction: "Genuine" as const, confidence: 0.91, created_at: "12:20" },
  { id: 4, kind: "cedar" as const, target: "CEDAR writer 7", prediction: "Genuine" as const, confidence: 0.86, created_at: "11:05" },
];

export const demoActivity = [
  { title: "User signature verified", detail: "Maya Patel · Genuine", time: "14:32" },
  { title: "User model trained", detail: "Maya Patel · 12 references", time: "14:05" },
  { title: "Identity registered", detail: "Rahul Iyer", time: "12:10" },
  { title: "CEDAR model trained", detail: "Writer 12", time: "10:47" },
];
