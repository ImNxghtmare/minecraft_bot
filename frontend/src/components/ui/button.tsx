import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
}

const buttonVariants =
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors " +
  "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:pointer-events-none"

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return <Comp className={cn(buttonVariants, className)} ref={ref} {...props} />
  }
)

Button.displayName = "Button"
