import { ModeToggle } from "@/components/mode-toggle"
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList } from "@/components/ui/breadcrumb"
import { Button } from "@/components/ui/button"
import { SidebarTrigger } from "@/components/ui/sidebar"

export const Header = () => {

    return (
        <div className="w-full w-full flex justify-between items-center p-2">
            <div className="w-max flex flex-row items-center gap-2">
                <SidebarTrigger />
                <Breadcrumb>
                    <BreadcrumbList>
                        <BreadcrumbItem>
                        <BreadcrumbLink href="/">Online map</BreadcrumbLink>
                        </BreadcrumbItem>
                    </BreadcrumbList>
                </Breadcrumb>
            </div>
            
            <div className="w-max flex flex-row items-center gap-2">
                <ModeToggle />
                <Button variant={"outline"}>
                    Sign In
                </Button>
            </div>
        </div>
    )
}