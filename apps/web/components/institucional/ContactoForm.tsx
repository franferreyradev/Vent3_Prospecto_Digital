'use client';

import { FormEvent, useState } from 'react';
import Input from '../ui/Input';
import Textarea from '../ui/Textarea';
import Button from '../ui/Button';

const EMAIL_CONTACTO = 'contacto@vent3.com.ar';

export default function ContactoForm() {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [mensaje, setMensaje] = useState('');

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const asunto = encodeURIComponent(`Consulta de ${nombre} — sitio web Vent3`);
    const cuerpo = encodeURIComponent(
      `Nombre: ${nombre}\nEmail: ${email}\n\nMensaje:\n${mensaje}`
    );

    window.location.href = `mailto:${EMAIL_CONTACTO}?subject=${asunto}&body=${cuerpo}`;
  }

  return (
    <form onSubmit={handleSubmit} className="flex max-w-md flex-col gap-4">
      <Input
        label="Nombre"
        type="text"
        required
        value={nombre}
        onChange={(e) => setNombre(e.target.value)}
      />
      <Input
        label="Email"
        type="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <Textarea
        label="Mensaje"
        required
        value={mensaje}
        onChange={(e) => setMensaje(e.target.value)}
      />
      <Button type="submit" variant="primary">
        Enviar consulta
      </Button>
    </form>
  );
}
