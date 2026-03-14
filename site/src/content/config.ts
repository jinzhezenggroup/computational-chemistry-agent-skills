import { defineCollection, z } from 'astro:content';

const skills = defineCollection({
  type: 'content',
  schema: z.object({
    name: z.string(),
    description: z.string().optional().default(''),
    compatibility: z.string().optional().default('-'),
    version: z.string().optional().default('-'),
    repository: z.string().optional(),
    sourcePath: z.string().optional(),
    category: z.string().optional()
  })
});

export const collections = { skills };
