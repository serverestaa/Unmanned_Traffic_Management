'use client'

import { useLazyGetMeQuery, useSigninMutation } from "@/api/user"
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
import { useAppDispatch } from "@/store/hooks"
import { setCurrentUser } from "@/api/user/slice"
import { saveToken } from "@/lib/tokenUtils"
 
const formSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6, "Password must be at least 6 characters long"),
})

export const SigninPage = () => {
    const router            = useRouter();
    const dispatch          = useAppDispatch();
    const [signin] = useSigninMutation()
    const [fetchMe]         = useLazyGetMeQuery();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  })
     
  const onSubmit = (values: z.infer<typeof formSchema>) => {
    toast.promise(
        signin(values).unwrap(),
        {
          loading: 'Signing in…',
          success: async ({ access_token }) => {
            saveToken(access_token);
            const user = await fetchMe().unwrap();
            dispatch(setCurrentUser(user));
            router.replace('/');
            return 'Signed in!';
          },
          error: (err) => `Signin failed: ${err.data?.message || err.message}`,
        }
      );
  
  }

  return (
    <div className="w-full flex flex-col items-center my-auto">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="w-full max-w-md space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input placeholder="example@gmail.com" {...field} />
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
                      <Input type="password" placeholder="********" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button variant="default" className="w-full mt-4" type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? "Submitting…" : "Sign In"}
              </Button>
              <TypographyP className="text-sm text-muted-foreground mx-auto w-full text-center">
                Don&apos;t have an account?{" "}
                <Link href="/signup" className="underline">
                  Sign up
                </Link>
              </TypographyP>
            </form>
          </Form>
    </div>
  )
}
