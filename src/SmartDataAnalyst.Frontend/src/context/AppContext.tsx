import { createContext, useContext, useState } from "react";
import { ReactNode } from "react";

interface AppContextType {
  currentFilename: string | null;
  setCurrentFilename: (name: string | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [currentFilename, setCurrentFilename] = useState<string | null>(null);

  return (
    <AppContext.Provider value={{ currentFilename, setCurrentFilename }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context)
    throw new Error("useAppContext must be used within AppProvider");
  return context;
};
