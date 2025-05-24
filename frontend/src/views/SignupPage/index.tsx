'use client'

import { useRegisterMutation } from "@/api/user"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { z } from "zod"
import { TypographyP } from "@/components/ui/typop"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { saveToken } from "@/lib/tokenUtils"

const formSchema = z.object({
  email:     z.string().email(),
  full_name: z.string().min(1, "Full name is required"),
  phone:     z.string().min(1, "Phone number is required"),
  role:      z.enum(["admin", "pilot"]),
  password:  z.string().min(6, "Password must be at least 6 characters long"),
})

export const SignupPage = () => {
    const router   = useRouter();
    const [signup] = useRegisterMutation()

  const form = useForm<z.infer<typeof formSchema>>({
    resolver:   zodResolver(formSchema),
    defaultValues: {
      email:     "",
      full_name: "",
      phone:     "",
      role:      "admin",
      password:  "",
    },
  })

  const onSubmit = (values: z.infer<typeof formSchema>) => {
    toast.promise(
        signup(values).unwrap(),
        {
          loading: 'Signing up…',
          success: ({ access_token }) => {
            saveToken(access_token);
            router.replace('/signin');
            return 'Account created. Please sign in!';
          },
          error: (err) => `Signup failed: ${err.data?.message || err.message}`,
        }
      );
  
  }

  return (
    <div className="w-full flex flex-col items-center my-auto">

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="w-full max-w-md space-y-4"
        >
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input placeholder="you@example.com" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="full_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Full Name</FormLabel>
                <FormControl>
                  <Input placeholder="John Doe" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Phone</FormLabel>
                <FormControl>
                  <Input placeholder="+1 555 123 4567" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button
            type="submit"
            className="w-full"
            disabled={form.formState.isSubmitting}
          >
            {form.formState.isSubmitting ? "Signing up…" : "Sign up"}
          </Button>
            <TypographyP className="text-sm text-muted-foreground mx-auto w-full text-center">
                Already have an account?{" "}
                <Link href="/signin" className="underline">
                Sign in
                </Link>
            </TypographyP>
        </form>
      </Form>
    </div>
  )
}
