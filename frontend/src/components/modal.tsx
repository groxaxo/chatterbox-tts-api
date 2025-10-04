"use client"

import * as React from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog"
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerFooter,
  DrawerTitle,
  DrawerDescription,
  DrawerTrigger,
  DrawerClose,
} from "@/components/ui/drawer"

// Hook to detect mobile - using simpler implementation to avoid potential issues
const useIsMobileSimple = (): boolean => {
  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    // Check if window is defined (client-side)
    if (typeof window === 'undefined') {
      return;
    }

    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    // Set initial value
    checkMobile();

    // Add event listener
    window.addEventListener('resize', checkMobile);

    // Cleanup
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return isMobile;
};

// 1. Create a Context to share the `isMobile` state
interface ModalContextType {
  isMobile: boolean;
}

const ModalContext = React.createContext<ModalContextType | undefined>(undefined);

const useModalContext = () => {
  const context = React.useContext(ModalContext);
  if (!context) {
    // Return default value instead of throwing to prevent crashes
    return { isMobile: false };
  }
  return context;
}

// --- Component Interfaces (mostly unchanged) ---
interface ModalProps {
  children: React.ReactNode
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

// 2. Modify the main Modal component to manage state and provide context
function Modal({ children, open, onOpenChange }: ModalProps) {
  const isMobile = useIsMobileSimple();
  const Component = isMobile ? Drawer : Dialog;

  return (
    <Component open={open} onOpenChange={onOpenChange}>
      {/* Provide the isMobile value to all children */}
      <ModalContext.Provider value={{ isMobile }}>
        {children}
      </ModalContext.Provider>
    </Component>
  );
}

// 3. Simplify all sub-components to use the context
function ModalTrigger({ children, ...props }: React.ComponentProps<typeof DialogTrigger>) {
  const { isMobile } = useModalContext();
  const Component = isMobile ? DrawerTrigger : DialogTrigger;
  return <Component {...props}>{children}</Component>;
}

function ModalContent({ className, children, ...props }: React.ComponentProps<typeof DialogContent>) {
  const { isMobile } = useModalContext();

  if (isMobile) {
    // DrawerContent has a different structure, often wrapping headers/footers
    return (
      <DrawerContent className={className} {...props}>
        {children}
      </DrawerContent>
    );
  }

  return (
    <DialogContent className={className} {...props}>
      {children}
    </DialogContent>
  );
}

function ModalHeader({ className, children, ...props }: React.ComponentProps<typeof DialogHeader>) {
  const { isMobile } = useModalContext();
  const Component = isMobile ? DrawerHeader : DialogHeader;
  return <Component className={className} {...props}>{children}</Component>;
}

function ModalFooter({ className, children, ...props }: React.ComponentProps<typeof DialogFooter>) {
  const { isMobile } = useModalContext();
  const Component = isMobile ? DrawerFooter : DialogFooter;
  return <Component className={className} {...props}>{children}</Component>;
}

function ModalTitle({ className, children, ...props }: React.ComponentProps<typeof DialogTitle>) {
  const { isMobile } = useModalContext();
  const Component = isMobile ? DrawerTitle : DialogTitle;
  return <Component className={className} {...props}>{children}</Component>;
}

function ModalDescription({ className, children, ...props }: React.ComponentProps<typeof DialogDescription>) {
  const { isMobile } = useModalContext();
  const Component = isMobile ? DrawerDescription : DialogDescription;
  return <Component className={className} {...props}>{children}</Component>;
}

function ModalClose({ className, children, ...props }: React.ComponentProps<typeof DialogClose>) {
  const { isMobile } = useModalContext();
  const Component = isMobile ? DrawerClose : DialogClose;
  return <Component className={className} {...props}>{children}</Component>;
}


export {
  Modal,
  ModalTrigger,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalTitle,
  ModalDescription,
  ModalClose,
}