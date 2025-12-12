import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// применяем Tailwind + clsx
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// BASE API URL
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
