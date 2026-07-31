import type { ReactNode } from "react"
import {
  Activity,
  BookOpen,
  Dna,
  FlaskConical,
  Home,
} from "lucide-react"

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
} from "@/components/ui/sidebar"

export type Crumb = {
  label: string
  href?: string
}

const NAV = [
  { title: "总览", href: "/", icon: Home },
  { title: "变异注释", href: "/tools/annotate/", icon: FlaskConical },
  { title: "引擎状态", href: "/tools/engines/", icon: Activity },
  { title: "API 说明", href: "/docs/", icon: BookOpen },
]

function isActive(href: string) {
  const path = window.location.pathname
  if (href === "/") return path === "/"
  return path === href || path.startsWith(href)
}

type AppShellProps = {
  title: string
  description?: string
  crumbs?: Crumb[]
  actions?: ReactNode
  children: ReactNode
}

export function AppShell({
  title,
  description,
  crumbs = [],
  actions,
  children,
}: AppShellProps) {
  return (
    <SidebarProvider>
      <Sidebar collapsible="icon">
        <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton size="lg" asChild>
                <a href="/">
                  <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                    <Dna className="size-4" />
                  </div>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold">online-biotools</span>
                    <span className="truncate text-xs text-muted-foreground">
                      annotation workspace
                    </span>
                  </div>
                </a>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>

        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>工作区</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {NAV.map((item) => (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive(item.href)}
                      tooltip={item.title}
                    >
                      <a href={item.href}>
                        <item.icon />
                        <span>{item.title}</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>

        <SidebarFooter>
          <div className="px-2 text-xs text-muted-foreground group-data-[collapsible=icon]:hidden">
            shadcn/ui · Monaco Editor
          </div>
        </SidebarFooter>
        <SidebarRail />
      </Sidebar>

      <SidebarInset>
        <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center gap-2 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem className="hidden md:block">
                <BreadcrumbLink href="/">online-biotools</BreadcrumbLink>
              </BreadcrumbItem>
              {crumbs.map((crumb, index) => (
                <span key={`${crumb.label}-${index}`} className="contents">
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    {crumb.href ? (
                      <BreadcrumbLink href={crumb.href}>{crumb.label}</BreadcrumbLink>
                    ) : (
                      <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
                    )}
                  </BreadcrumbItem>
                </span>
              ))}
            </BreadcrumbList>
          </Breadcrumb>
          {actions ? <div className="ml-auto flex items-center gap-2">{actions}</div> : null}
        </header>

        <div className="flex flex-1 flex-col gap-6 p-4 md:p-6">
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            {description ? (
              <p className="text-sm text-muted-foreground">{description}</p>
            ) : null}
          </div>
          {children}
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
