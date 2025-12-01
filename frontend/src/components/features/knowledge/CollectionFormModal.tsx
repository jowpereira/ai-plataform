import { useForm, type ControllerRenderProps } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Loader2, FolderPlus } from "lucide-react";

const formSchema = z.object({
  name: z.string().min(3, "Nome deve ter pelo menos 3 caracteres"),
  description: z.string().optional(),
  namespace: z.string().optional(),
  tags: z.string().optional(), // Comma separated
});

type CollectionFormValues = z.infer<typeof formSchema>;

interface CollectionFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: {
    name: string;
    description?: string;
    namespace?: string;
    tags?: string[];
  }) => Promise<void>;
  isSaving: boolean;
}

export function CollectionFormModal({
  open,
  onOpenChange,
  onSubmit,
  isSaving,
}: CollectionFormModalProps) {
  const form = useForm<CollectionFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      description: "",
      namespace: "",
      tags: "",
    },
  });

  const handleSubmit = async (values: CollectionFormValues) => {
    try {
      await onSubmit({
        name: values.name,
        description: values.description,
        namespace: values.namespace || undefined,
        tags: values.tags
          ? values.tags
              .split(",")
              .map((tag: string) => tag.trim())
              .filter((tag) => tag.length > 0)
          : undefined,
      });
      form.reset();
      onOpenChange(false);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 rounded-xl">
              <FolderPlus className="h-5 w-5 text-primary" />
            </div>
            <div>
              <DialogTitle>Nova Coleção</DialogTitle>
              <DialogDescription>
                Crie uma coleção para agrupar documentos relacionados.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }: { field: ControllerRenderProps<CollectionFormValues, "name"> }) => (
                <FormItem>
                  <FormLabel>Nome</FormLabel>
                  <FormControl>
                    <Input placeholder="Ex: Manuais de Produto" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }: { field: ControllerRenderProps<CollectionFormValues, "description"> }) => (
                <FormItem>
                  <FormLabel>Descrição</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Descreva o conteúdo desta coleção..."
                      className="resize-none"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="namespace"
                render={({ field }: { field: ControllerRenderProps<CollectionFormValues, "namespace"> }) => (
                  <FormItem>
                    <FormLabel>Namespace (Opcional)</FormLabel>
                    <FormControl>
                      <Input placeholder="Ex: produtos" {...field} />
                    </FormControl>
                    <FormDescription className="text-xs">
                      Identificador de isolamento lógico
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="tags"
                render={({ field }: { field: ControllerRenderProps<CollectionFormValues, "tags"> }) => (
                  <FormItem>
                    <FormLabel>Tags (Opcional)</FormLabel>
                    <FormControl>
                      <Input placeholder="vendas, 2024" {...field} />
                    </FormControl>
                    <FormDescription className="text-xs">
                      Separadas por vírgula
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter className="pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSaving}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={isSaving}>
                {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Criar Coleção
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
