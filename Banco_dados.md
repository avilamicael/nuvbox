● Aqui estão as principais queries que você pode rodar:

  1. Ver todos os fragmentos

  docker exec cerebro-postgres psql -U cerebro -d cerebro_db -c "SELECT id, resumo, importance_score FROM fragmentos
   ORDER BY criado_em DESC LIMIT 20;"

  2. Ver entidades (pessoas, projetos, etc)

  docker exec cerebro-postgres psql -U cerebro -d cerebro_db -c "SELECT id, nome, tipo, frequencia FROM entidades
  ORDER BY frequencia DESC LIMIT 30;"

  3. Ver tópicos hierárquicos

  docker exec cerebro-postgres psql -U cerebro -d cerebro_db -c "SELECT id, caminho, frequencia, nivel FROM topicos
  ORDER BY frequencia DESC LIMIT 20;"

  4. Ver ações por status

  docker exec cerebro-postgres psql -U cerebro -d cerebro_db -c "SELECT status, COUNT(*) FROM action_items GROUP BY
  status;"

  5. Ver fragmentos com maior importance

  docker exec cerebro-postgres psql -U cerebro -d cerebro_db -c "SELECT id, resumo, importance_score FROM fragmentos
   WHERE importance_score > 0.5 ORDER BY importance_score DESC;"

  6. Ver fragmentos por tópico

  docker exec cerebro-postgres psql -U cerebro -d cerebro_db -c "SELECT t.caminho, COUNT(f.id) as total FROM
  fragmento_topico ft JOIN topicos t ON t.id = ft.topico_id JOIN fragmentos f ON f.id = ft.fragmento_id GROUP BY
  t.caminho ORDER BY total DESC;"

  7. Ver fragmentos por entidade

  docker exec cerebro-postgres psql -U cerebro -d cerebro_db -c "SELECT e.nome, COUNT(f.id) as total FROM
  fragmento_entidade fe JOIN entidades e ON e.id = fe.entidade_id JOIN fragmentos f ON f.id = fe.fragmento_id GROUP
  BY e.nome ORDER BY total DESC LIMIT 20;"

  8. Ver transcrições pendentes de processar

  docker exec cerebro-postgres psql -U cerebro -d cerebro_db -c "SELECT id, texto, status FROM transcricoes WHERE
  status = 'pending' LIMIT 10;"

  9. Ver logs de processamento

  docker exec cerebro-postgres psql -U cerebro -d cerebro_db -c "SELECT id, status, modulo4_erro FROM transcricoes
  WHERE status != 'pending' ORDER BY processado_em DESC LIMIT 20;"

  10. Ver schema completo da tabela action_items

  docker exec cerebro-postgres psql -U cerebro -d cerebro_db -c "\d action_items"
