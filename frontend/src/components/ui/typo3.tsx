import { FC } from "react"

interface Props extends React.HTMLAttributes<HTMLHeadingElement> {
    className?: string
    children?: React.ReactNode
    style?: React.CSSProperties 
}

export const TypographyH3: FC<Props> = ({className, style, children}) => {
    return (
      <h3 className={`scroll-m-20 text-2xl font-semibold tracking-tight ${className}`} style={style}>
        {children}
      </h3>
    )
  }
  