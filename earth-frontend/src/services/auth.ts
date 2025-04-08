
import { User } from "@/types/models";

// Mock user database for authentication
const MOCK_USERS = [
  {
    id: "1",
    name: "Admin User",
    email: "admin@planet-earth.com",
    avatar: "https://api.dicebear.com/7.x/bottts/svg?seed=admin",
    role: "admin" as const,
    password: "admin123", // In a real app, this would be hashed
  },
  {
    id: "2",
    name: "Regular User",
    email: "user@planet-earth.com",
    avatar: "https://api.dicebear.com/7.x/bottts/svg?seed=user",
    role: "user" as const,
    password: "user123",
  },
  {
    id: "3",
    name: "View Only",
    email: "viewer@planet-earth.com",
    avatar: "https://api.dicebear.com/7.x/bottts/svg?seed=viewer",
    role: "viewer" as const,
    password: "viewer123",
  },
];

// Simulate login functionality
export const loginUser = async (
  email: string,
  password: string
): Promise<User | null> => {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 800));

  const user = MOCK_USERS.find(
    (u) => u.email === email && u.password === password
  );

  if (user) {
    // Don't return the password
    const { password, ...userWithoutPassword } = user;
    
    // Save user to localStorage
    localStorage.setItem("planet-earth-user", JSON.stringify(userWithoutPassword));
    
    return userWithoutPassword;
  }

  return null;
};

// Get the current user from localStorage
export const getCurrentUser = (): User | null => {
  const userJson = localStorage.getItem("planet-earth-user");
  if (userJson) {
    return JSON.parse(userJson);
  }
  return null;
};

// Logout the current user
export const logoutUser = (): void => {
  localStorage.removeItem("planet-earth-user");
};

// Check if the current user has the required role
export const hasRole = (
  user: User | null,
  roles: ("admin" | "user" | "viewer")[]
): boolean => {
  if (!user) return false;
  return roles.includes(user.role);
};

// Check if the current user can perform a specific action
export const canPerformAction = (
  user: User | null,
  action: "create" | "read" | "update" | "delete"
): boolean => {
  if (!user) return false;
  
  switch (action) {
    case "read":
      return true; // All roles can read
    case "create":
    case "update":
      return user.role === "admin" || user.role === "user";
    case "delete":
      return user.role === "admin";
    default:
      return false;
  }
};
