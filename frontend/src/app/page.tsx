"use client";
import React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";

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
          <p className="text-red-700">
            За нарушение правил использования воздушного пространства предусмотрен штраф в размере 10 МРП (39,3 тыс. тг) 
            для физлиц или 20 МРП (78,6 тыс. тг) для юридических лиц. Возможна конфискация беспилотника.
          </p>
          <Separator />
          {!localStorage.getItem('agreed_to_terms_and_services') && (
            <div className="flex flex-col gap-4">
              <label className="inline-flex items-center space-x-2">
                <input
                  type="checkbox"
                  className="form-checkbox h-5 w-5 text-teal-600 transition duration-150 ease-in-out"
                />
                <span className="text-gray-700">Я прочитал и понимаю</span>
              </label>
              <Button className="w-32" onClick={()=>{
                if (!localStorage.getItem('agreed_to_terms_and_services')){
                  localStorage.setItem('agreed_to_terms_and_services', "true");
                }
              }}>
                Согласится
              </Button>
            </div>
          )}
          <p>
            Когда всё готово — крепко пристегнись, проверь дрон и управляй осторожно. Удачи в полётах! 🚁✨
          </p>
        </CardContent>
      </Card>
    </main>
  );
}

