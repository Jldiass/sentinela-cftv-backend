import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { Camera, CameraInput, CameraUpdate } from "../types/api";
const schema = z.object({
  name: z.string().trim().min(2, "Informe ao menos 2 caracteres").max(100),
  location: z.string().max(160),
  audio_enabled: z.boolean(),
  pre_alarm_seconds: z.coerce.number().int().min(0).max(300),
  post_alarm_seconds: z.coerce.number().int().min(1).max(600),
  enabled: z.boolean(),
});
export type CameraFormValues = z.infer<typeof schema>;
export function CameraForm({
  camera,
  onSubmit,
  busy,
  onCancel,
}: {
  camera?: Camera;
  onSubmit: (values: CameraInput | CameraUpdate) => void;
  busy: boolean;
  onCancel: () => void;
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CameraFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      location: "",
      audio_enabled: true,
      pre_alarm_seconds: 30,
      post_alarm_seconds: 60,
      enabled: true,
    },
  });
  useEffect(() => {
    if (camera) reset(camera);
  }, [camera, reset]);
  return (
    <form
      className="form-grid"
      onSubmit={handleSubmit((values) => {
        const createInput: CameraInput = {
          name: values.name,
          location: values.location,
          audio_enabled: values.audio_enabled,
          pre_alarm_seconds: values.pre_alarm_seconds,
          post_alarm_seconds: values.post_alarm_seconds,
        };
        onSubmit(camera ? values : createInput);
      })}
    >
      <label className="field field-wide">
        Nome
        <input autoFocus {...register("name")} />
        <em>{errors.name?.message}</em>
      </label>
      <label className="field field-wide">
        Localização
        <input {...register("location")} />
        <em>{errors.location?.message}</em>
      </label>
      <label className="field">
        Pré-alarme (segundos)
        <input type="number" {...register("pre_alarm_seconds")} />
        <em>{errors.pre_alarm_seconds?.message}</em>
      </label>
      <label className="field">
        Pós-alarme (segundos)
        <input type="number" {...register("post_alarm_seconds")} />
        <em>{errors.post_alarm_seconds?.message}</em>
      </label>
      <label className="toggle field-wide">
        <input type="checkbox" {...register("audio_enabled")} /> Áudio habilitado para esta câmera
      </label>
      {camera && (
        <label className="toggle field-wide">
          <input type="checkbox" {...register("enabled")} /> Câmera habilitada para publicação e monitoramento
        </label>
      )}
      <footer className="modal-actions">
        <button type="button" className="button ghost" onClick={onCancel}>
          Cancelar
        </button>
        <button className="button primary" disabled={busy}>
          {busy ? "Salvando..." : camera ? "Salvar alterações" : "Cadastrar câmera"}
        </button>
      </footer>
    </form>
  );
}
