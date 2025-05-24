import { FC } from 'react';

interface Props extends React.HTMLAttributes<HTMLParagraphElement> {
  className?: string;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}

export const TypographyP: FC<Props> = ({ className, style, children }) => {
  return (
    <p className={`${className}`} style={style}>
      {children}
    </p>
  );
};
