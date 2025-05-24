import { FC } from "react"

interface Props extends React.HTMLAttributes<HTMLHeadingElement> {
    className?: string
    children?: React.ReactNode
    style?: React.CSSProperties 
}

export const TypographyH1: FC<Props> = ({className, style, children}) => {
    return (
      <h1 className={`scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl ${className}`} style={style}>
        {children}
      </h1>
    )
  }
  