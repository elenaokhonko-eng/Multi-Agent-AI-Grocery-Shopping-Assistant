import { createContext, useContext, useEffect, useState } from "react";
import { UserProfile } from "@/types/user-profile";
import { loadUserProfile, saveUserProfile } from "@/lib/user-profile";

type Ctx = {
  profile: UserProfile;
  setProfile: (u: UserProfile) => void;
  update: <K extends keyof UserProfile>(key: K, value: UserProfile[K]) => void;
};

const UserProfileContext = createContext<Ctx | null>(null);

export const UserProfileProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [profile, setProfile] = useState<UserProfile>(loadUserProfile());

  useEffect(() => {
    saveUserProfile(profile);
  }, [profile]);

  const update: Ctx["update"] = (key, value) => {
    setProfile((p) => ({ ...p, [key]: value }));
  };

  return (
    <UserProfileContext.Provider value={{ profile, setProfile, update }}>
      {children}
    </UserProfileContext.Provider>
  );
};

export const useUserProfile = () => {
  const ctx = useContext(UserProfileContext);
  if (!ctx) throw new Error("useUserProfile must be used within UserProfileProvider");
  return ctx;
};
