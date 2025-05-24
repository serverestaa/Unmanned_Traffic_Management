import { ModeToggle } from "@/components/mode-toggle"
import { Button } from "@/components/ui/button"
import { TypographyH3 } from "@/components/ui/typo3"

export const Header = () => {

    return (
        <div className="w-full w-full flex justify-between items-center p-4">
            <TypographyH3>
                Decedron
            </TypographyH3>
            <div className="w-max flex flex-row items-center gap-2">
                <ModeToggle />
                <Button variant={"outline"}>
                    Sign In
                </Button>
            </div>
        </div>
    )
}