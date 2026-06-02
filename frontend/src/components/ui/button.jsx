import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        // Ação primária POSITIVA (Guardar/Aprovar/Submeter/Criar/Entrar…).
        primary:
          "bg-floresta text-white shadow hover:bg-floresta-dark",
        // Ação DESTRUTIVA/negativa (Apagar/Rejeitar/Suspender…) → outline Carmesim.
        destructive:
          "bg-white border border-carmesim text-carmesim shadow-sm hover:bg-carmesim-50",
        // Só para confirmação IRREVERSÍVEL dentro de diálogo ("Apagar definitivamente").
        destructiveSolid:
          "bg-carmesim text-white shadow-sm hover:bg-carmesim-dark",
        // DEPRECADA para botões: usar `primary` (positiva) ou `destructive`/`destructiveSolid`.
        // Mantida só para não partir usos existentes; não usar como CTA genérico.
        brand:
          "bg-carmesim text-white shadow hover:bg-carmesim-dark",
        outline:
          "border border-input shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3 text-xs",
        lg: "h-11 rounded-md px-8",
        icon: "h-11 w-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props} />
  );
})
Button.displayName = "Button"

export { Button, buttonVariants }
