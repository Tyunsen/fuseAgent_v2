'use client';

import {
  CollectionConfigCreationModeEnum,
  CollectionConfigGraphEngineEnum,
  ModelSpec,
  TitleGenerateRequestLanguageEnum,
  type CollectionConfig,
} from '@/api';
import { useCollectionContext } from '@/components/providers/collection-provider';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { apiClient } from '@/lib/api/client';
import { cn, objectKeys } from '@/lib/utils';
import { zodResolver } from '@hookform/resolvers/zod';
import _ from 'lodash';
import { useLocale, useTranslations } from 'next-intl';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { toast } from 'sonner';
import * as z from 'zod';
import { isMirofishCollection } from './tools';

const collectionSchema = z.object({
  title: z.string().trim().min(1),
  description: z.string().trim().min(1),
  type: z.literal('document'),
  config: z.any().optional(),
});

type FormValueType = {
  title: string;
  description: string;
  type: 'document';
  config?: CollectionConfig;
};

export type ProviderModel = {
  label?: string;
  name?: string;
  models?: ModelSpec[];
};

const legacyDefaultConfig = (locale: string): CollectionConfig => ({
  source: 'system',
  enable_fulltext: true,
  enable_knowledge_graph: true,
  enable_vector: true,
  enable_summary: false,
  enable_vision: false,
  completion: {
    custom_llm_provider: '',
    model: '',
    model_service_provider: '',
  },
  embedding: {
    custom_llm_provider: '',
    model: '',
    model_service_provider: '',
  },
  language: (Object.values(TitleGenerateRequestLanguageEnum).includes(
    locale as TitleGenerateRequestLanguageEnum,
  )
    ? locale
    : 'zh-CN') as TitleGenerateRequestLanguageEnum,
  creation_mode: CollectionConfigCreationModeEnum.aperag_advanced,
  graph_engine: CollectionConfigGraphEngineEnum.lightrag,
});

const mirofishConfigSeed = (locale: string): CollectionConfig => ({
  source: 'system',
  enable_fulltext: true,
  enable_knowledge_graph: false,
  enable_vector: true,
  enable_summary: false,
  enable_vision: false,
  language: (Object.values(TitleGenerateRequestLanguageEnum).includes(
    locale as TitleGenerateRequestLanguageEnum,
  )
    ? locale
    : 'zh-CN') as TitleGenerateRequestLanguageEnum,
  creation_mode: CollectionConfigCreationModeEnum.mirofish_simple,
  graph_engine: CollectionConfigGraphEngineEnum.mirofish,
});

export const CollectionForm = ({ action }: { action: 'add' | 'edit' }) => {
  const router = useRouter();
  const { collection, loadCollection } = useCollectionContext();
  const [completionModels, setCompletionModels] = useState<ProviderModel[]>();
  const [embeddingModels, setEmbeddingModels] = useState<ProviderModel[]>();

  const common_tips = useTranslations('common.tips');
  const common_action = useTranslations('common.action');
  const page_collections = useTranslations('page_collections');
  const locale = useLocale();
  const requiredMessage =
    locale === 'zh-CN' ? '必填项不能为空。' : 'This field is required.';

  const minimalMode =
    action === 'add' || isMirofishCollection(collection?.config);

  const defaultValues = useMemo<FormValueType>(() => {
    if (action === 'add') {
      return {
        title: '',
        description: '',
        type: 'document',
        config: mirofishConfigSeed(locale),
      };
    }

    return {
      title: collection?.title || '',
      description: collection?.description || '',
      type: 'document',
      config:
        collection?.config ||
        (minimalMode
          ? mirofishConfigSeed(locale)
          : legacyDefaultConfig(locale)),
    };
  }, [
    action,
    collection?.config,
    collection?.description,
    collection?.title,
    locale,
    minimalMode,
  ]);

  const CollectionConfigIndexTypes = {
    'config.enable_vector': {
      disabled: true,
      title: page_collections('index_type_VECTOR.title'),
      description: page_collections('index_type_VECTOR.description'),
    },
    'config.enable_fulltext': {
      disabled: true,
      title: page_collections('index_type_FULLTEXT.title'),
      description: page_collections('index_type_FULLTEXT.description'),
    },
    'config.enable_knowledge_graph': {
      disabled: false,
      title: page_collections('index_type_GRAPH.title'),
      description: page_collections('index_type_GRAPH.description'),
    },
    'config.enable_summary': {
      disabled: false,
      title: page_collections('index_type_SUMMARY.title'),
      description: page_collections('index_type_SUMMARY.description'),
    },
    'config.enable_vision': {
      disabled: false,
      title: page_collections('index_type_VISION.title'),
      description: page_collections('index_type_VISION.description'),
    },
  } as const;

  const form = useForm<FormValueType>({
    resolver: zodResolver(collectionSchema),
    defaultValues,
  });

  useEffect(() => {
    form.reset(defaultValues);
  }, [defaultValues, form]);

  const loadModels = useCallback(async () => {
    if (minimalMode) {
      setCompletionModels([]);
      setEmbeddingModels([]);
      return;
    }

    const res = await apiClient.defaultApi.availableModelsPost({
      tagFilterRequest: {
        tag_filters: [{ operation: 'AND', tags: ['enable_for_collection'] }],
      },
    });
    const completion = res.data.items?.map((m) => ({
      label: m.label,
      name: m.name,
      models: m.completion,
    }));
    const embedding = res.data.items?.map((m) => ({
      label: m.label,
      name: m.name,
      models: m.embedding,
    }));
    setCompletionModels(completion || []);
    setEmbeddingModels(embedding || []);
  }, [minimalMode]);

  const completionModelName = useWatch({
    control: form.control,
    name: 'config.completion.model',
  });

  useEffect(() => {
    if (minimalMode || _.isEmpty(completionModels)) {
      return;
    }

    let defaultModel: ModelSpec | undefined;
    let currentModel: ModelSpec | undefined;
    let defaultProvider: ProviderModel | undefined;
    let currentProvider: ProviderModel | undefined;

    completionModels?.forEach((provider) => {
      provider.models?.forEach((model) => {
        if (
          model.tags?.some((tag) => tag === 'default_for_collection_completion')
        ) {
          defaultModel = model;
          defaultProvider = provider;
        }
        if (model.model === completionModelName) {
          currentModel = model;
          currentProvider = provider;
        }
      });
    });

    form.setValue(
      'config.completion.custom_llm_provider',
      currentModel?.custom_llm_provider || '',
    );
    form.setValue(
      'config.completion.model_service_provider',
      currentProvider?.name || defaultProvider?.name || '',
    );
    form.setValue(
      'config.completion.model',
      currentModel?.model || defaultModel?.model || '',
    );
  }, [completionModelName, completionModels, form, minimalMode]);

  const embeddingModelName = useWatch({
    control: form.control,
    name: 'config.embedding.model',
  });

  useEffect(() => {
    if (minimalMode || _.isEmpty(embeddingModels)) {
      return;
    }

    let defaultModel: ModelSpec | undefined;
    let currentModel: ModelSpec | undefined;
    let defaultProvider: ProviderModel | undefined;
    let currentProvider: ProviderModel | undefined;

    embeddingModels?.forEach((provider) => {
      provider.models?.forEach((model) => {
        if (model.tags?.some((tag) => tag === 'default_for_embedding')) {
          defaultModel = model;
          defaultProvider = provider;
        }
        if (model.model === embeddingModelName) {
          currentModel = model;
          currentProvider = provider;
        }
      });
    });

    form.setValue(
      'config.embedding.custom_llm_provider',
      currentModel?.custom_llm_provider || '',
    );
    form.setValue(
      'config.embedding.model_service_provider',
      currentProvider?.name || defaultProvider?.name || '',
    );
    form.setValue(
      'config.embedding.model',
      currentModel?.model || defaultModel?.model || '',
    );
  }, [embeddingModelName, embeddingModels, form, minimalMode]);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const validateAdvancedConfig = useCallback(
    (values: FormValueType) => {
      if (minimalMode) {
        return true;
      }

      if (
        values.config?.enable_vector &&
        _.isEmpty(values.config.embedding?.model)
      ) {
        form.setError('config.embedding.model', {
          type: 'manual',
          message: requiredMessage,
        });
        return false;
      }

      if (
        (values.config?.enable_knowledge_graph ||
          values.config?.enable_summary ||
          values.config?.enable_vision) &&
        _.isEmpty(values.config.completion?.model)
      ) {
        form.setError('config.completion.model', {
          type: 'manual',
          message: requiredMessage,
        });
        return false;
      }

      return true;
    },
    [form, minimalMode, requiredMessage],
  );

  const handleCreateOrUpdate = useCallback(
    async (values: FormValueType) => {
      if (!validateAdvancedConfig(values)) {
        return;
      }

      if (action === 'edit') {
        if (!collection?.id) {
          return;
        }

        const updatePayload = {
          title: values.title,
          description: values.description,
          config:
            values.config ||
            collection.config ||
            (minimalMode
              ? mirofishConfigSeed(locale)
              : legacyDefaultConfig(locale)),
        };

        const res = await apiClient.defaultApi.collectionsCollectionIdPut({
          collectionId: collection.id,
          collectionUpdate: updatePayload,
        });
        if (res.data.id) {
          toast.success(common_tips('update_success'));
          await loadCollection();
        }
        return;
      }

      const createPayload = minimalMode
        ? {
            title: values.title,
            description: values.description,
            type: values.type,
            config: {
              ...mirofishConfigSeed(locale),
              source: values.config?.source || 'system',
              language:
                values.config?.language ||
                (locale as TitleGenerateRequestLanguageEnum),
            },
          }
        : values;

      const res = await apiClient.defaultApi.collectionsPost({
        collectionCreate: createPayload,
      });
      if (res.data.id) {
        toast.success(common_tips('create_success'));
        router.push(`/workspace/collections/${res.data.id}/documents/upload`);
      }
    },
    [
      action,
      collection?.config,
      collection?.id,
      common_tips,
      loadCollection,
      locale,
      minimalMode,
      router,
      validateAdvancedConfig,
    ],
  );

  const minimalHint =
    locale === 'zh-CN'
      ? '创建后会直接进入文档页。首次添加文档时，系统会自动开始首次建图。'
      : 'After creation you will land on the document page, and the first confirmed upload will start the initial graph build automatically.';

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(handleCreateOrUpdate)}
        className="flex flex-col gap-4"
      >
        <Card>
          <CardHeader>
            <CardTitle>{page_collections('general')}</CardTitle>
            <CardDescription>{minimalMode ? minimalHint : ''}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-6">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{page_collections('name')}</FormLabel>
                  <FormControl>
                    <Input
                      className="md:w-6/12"
                      placeholder={page_collections('name_placeholder')}
                      {...field}
                      value={field.value || ''}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{page_collections('description')}</FormLabel>
                  <FormControl>
                    <Textarea
                      className="h-38"
                      placeholder={page_collections('description_placeholder')}
                      {...field}
                      value={field.value || ''}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {!minimalMode && (
              <FormField
                control={form.control}
                name="config.language"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{page_collections('language')}</FormLabel>
                    <FormControl>
                      <RadioGroup
                        value={field.value}
                        onValueChange={field.onChange}
                        className="mt-2 flex flex-row items-center gap-4"
                      >
                        <Label>
                          <RadioGroupItem value="zh-CN" />
                          {page_collections('language_zh_CN')}
                        </Label>
                        <Label>
                          <RadioGroupItem value="en-US" />
                          {page_collections('language_en_US')}
                        </Label>
                      </RadioGroup>
                    </FormControl>
                  </FormItem>
                )}
              />
            )}

            {minimalMode && (
              <div className="bg-accent/30 flex flex-wrap items-center gap-2 rounded-lg border px-3 py-2 text-sm">
                <Badge variant="secondary">
                  {locale === 'zh-CN' ? '自动处理' : 'Automatic'}
                </Badge>
                <span className="text-muted-foreground">
                  {locale === 'zh-CN'
                    ? '向量/全文检索默认开启，图谱流程按 MiroFish 方式在文档确认后自动执行。'
                    : 'Vector/full-text retrieval stays enabled, and the MiroFish graph flow starts automatically after document confirmation.'}
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        {!minimalMode && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>{page_collections('index_types')}</CardTitle>
                <CardDescription>
                  {page_collections('index_types_description')}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                {objectKeys(CollectionConfigIndexTypes).map((key) => {
                  const item = CollectionConfigIndexTypes[key];
                  return (
                    <FormField
                      key={key}
                      control={form.control}
                      name={key}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel
                            className={cn(
                              'has-[[aria-checked=true]]:bg-accent/50 flex items-center gap-3 rounded-lg border p-3',
                              item.disabled
                                ? 'cursor-not-allowed'
                                : 'hover:bg-accent/30 cursor-pointer',
                            )}
                          >
                            <div className="grid gap-2">
                              <div className="flex items-center gap-2 leading-none font-medium">
                                {item.title}
                                {item.disabled && (
                                  <Badge>{page_collections('required')}</Badge>
                                )}
                              </div>
                              <p className="text-muted-foreground text-sm font-medium">
                                {item.description}
                              </p>
                            </div>
                            <FormControl className="ml-auto">
                              <Switch
                                checked={Boolean(field.value)}
                                disabled={item.disabled}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                          </FormLabel>
                        </FormItem>
                      )}
                    />
                  );
                })}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{page_collections('model_settings')}</CardTitle>
                <CardDescription>
                  {page_collections('model_settings_description')}
                </CardDescription>
              </CardHeader>

              <CardContent className="flex flex-col gap-6 pt-6">
                <FormField
                  control={form.control}
                  name="config.embedding.model"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        {page_collections('embedding_model')}
                      </FormLabel>
                      <FormControl className="ml-auto">
                        <Select
                          {...field}
                          onValueChange={field.onChange}
                          value={field.value || ''}
                        >
                          <SelectTrigger className="w-full cursor-pointer md:w-6/12">
                            <SelectValue placeholder="Select a model" />
                          </SelectTrigger>
                          <SelectContent>
                            {embeddingModels
                              ?.filter((item) => _.size(item.models))
                              .map((item) => (
                                <SelectGroup key={item.name}>
                                  <SelectLabel>{item.label}</SelectLabel>
                                  {item.models?.map((model) => (
                                    <SelectItem
                                      key={model.model}
                                      value={model.model || ''}
                                    >
                                      {model.model}
                                    </SelectItem>
                                  ))}
                                </SelectGroup>
                              ))}
                          </SelectContent>
                        </Select>
                      </FormControl>
                      <FormDescription>
                        {page_collections('embedding_model_description')}
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Separator />

                <FormField
                  control={form.control}
                  name="config.completion.model"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        {page_collections('completion_model')}
                      </FormLabel>
                      <FormControl className="ml-auto">
                        <Select
                          {...field}
                          onValueChange={field.onChange}
                          value={field.value || ''}
                        >
                          <SelectTrigger className="w-full cursor-pointer md:w-6/12">
                            <SelectValue placeholder="Select a model" />
                          </SelectTrigger>
                          <SelectContent>
                            {completionModels
                              ?.filter((item) => _.size(item.models))
                              .map((item) => (
                                <SelectGroup key={item.name}>
                                  <SelectLabel>{item.label}</SelectLabel>
                                  {item.models?.map((model) => (
                                    <SelectItem
                                      key={model.model}
                                      value={model.model || ''}
                                    >
                                      {model.model}
                                    </SelectItem>
                                  ))}
                                </SelectGroup>
                              ))}
                          </SelectContent>
                        </Select>
                      </FormControl>
                      <FormDescription>
                        {page_collections('completion_model_description')}
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>
          </>
        )}

        <div className="flex justify-end gap-4">
          {action === 'add' && (
            <Button variant="outline" asChild>
              <Link href="/workspace/collections">
                {common_action('cancel')}
              </Link>
            </Button>
          )}
          <Button type="submit" className="cursor-pointer px-6">
            {action === 'add'
              ? page_collections('create_collection')
              : page_collections('update_collection')}
          </Button>
        </div>
      </form>
    </Form>
  );
};
