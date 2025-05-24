import { FC } from "react"

interface Props extends React.HTMLAttributes<HTMLHeadingElement> {
    className?: string
    children?: React.ReactNode
    style?: React.CSSProperties 
}

export const TypographyH2: FC<Props> = ({className, style, children}) => {
    return (
      <h2 className={`scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight first:mt-0 ${className}`} style={style}>
        {children}
      </h2>
    )
  }
  