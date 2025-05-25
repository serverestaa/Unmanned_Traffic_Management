"use client";
import React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export default function Home() {
  return (
    <main className="container mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle>Привет, пилот!</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p>
            Прежде чем отправиться в полёт над городом, убедись, что у тебя на руках все необходимые документы:
          </p>
          <ol className="list-decimal list-inside pl-4 space-y-2">
            <li>
              <strong>Свидетельство о постановке на учёт БАС и сертификат оператора</strong>
              <p>
                Это базовый «пластик», который подтверждает, что твоя беспилотная система зарегистрирована, а ты — допущен к управлению.
                <Link
                  href="https://caa.gov.kz/ru/uchet-bpla"
                  className="text-blue-600 underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Узнай подробнее по ссылке
                </Link>
                .
              </p>
            </li>
            <li>
              <strong>Разрешение на полёты над густонаселёнными районами</strong>
              <p>
                Твой дрон весит более 0,25 кг? Тогда без разрешения от Авиационной администрации (АО «Авиационная администрация») не обойтись. Это важно для безопасности людей и зданий внизу.
              </p>
            </li>
            <li>
              <strong>Сертификат оператора категории 1</strong>
              <p>
                Чтобы получить этот документ, нужно пройти теоретическое обучение. Это защитит тебя и окружающих в сложных воздушных ситуациях.
              </p>
            </li>
          </ol>
          <Separator />
          <p>
            Когда всё готово — крепко пристегнись, проверь дрон и управляй осторожно. Удачи в полётах! 🚁✨
          </p>
        </CardContent>
      </Card>
    </main>
  );
}

