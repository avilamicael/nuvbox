"""
Canal HTTP para Curadoria de Dados — Módulo 6.

Expõe endpoints GET/PATCH/DELETE para que o usuário revise e corrija:
- Fragmentos (resumos)
- Entidades (nomes, descrições, status; soft delete)
- Tópicos (caminhos hierárquicos; soft delete)
- Action Items (tarefas)
- Correções de texto (mapeamentos errado→correto aplicados antes do LLM)

Todos os endpoints requerem X-Cerebro-Secret / X-Jarvis-Secret e filtram por usuario_id=1 (MVP).
"""

from flask import Flask, request, jsonify
from config import settings
from utils import setup_logger
from modulo3_armazenamento.db import get_connection

logger = setup_logger(__name__)

USUARIO_ID = 1  # MVP: single user


def register_dados_routes(app: Flask) -> None:
    """
    Registra os endpoints /dados/* em um Flask app existente.

    Args:
        app: Flask application instance

    Endpoints:
        GET  /dados/fragmentos              — list de fragmentos com paginação
        PATCH /dados/fragmentos/<id>        — atualizar resumo
        GET  /dados/entidades               — list de entidades com filtros
        PATCH /dados/entidades/<id>         — atualizar nome/descrição/status
        GET  /dados/topicos                 — list de tópicos
        PATCH /dados/topicos/<id>           — atualizar caminho/descrição
        GET  /dados/action-items            — list de tarefas
        PATCH /dados/action-items/<id>      — atualizar status/texto
    """

    def _check_auth():
        """Validar secret header (mesmo padrão do M1/M6)."""
        secret = (
            request.headers.get("X-Jarvis-Secret")
            or request.headers.get("X-Cerebro-Secret")
            or ""
        )
        if secret != settings.flask.webhook_secret:
            logger.warning(
                f"❌ Unauthorized /dados attempt from {request.remote_addr}"
            )
            return False
        return True

    # ─────────────────────────────────────────────────────────────
    # FRAGMENTOS
    # ─────────────────────────────────────────────────────────────

    @app.route("/dados/fragmentos", methods=["GET"])
    def get_fragmentos():
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            page = request.args.get("page", 1, type=int)
            limit = request.args.get("limit", 20, type=int)
            busca = request.args.get("busca", "", type=str).strip()

            limit = min(limit, 100)  # Max 100 per request
            offset = (page - 1) * limit

            with get_connection() as conn:
                cursor = conn.cursor()

                # Query base
                where_clause = "WHERE usuario_id = %s"
                params = [USUARIO_ID]

                if busca:
                    where_clause += " AND resumo ILIKE %s"
                    params.append(f"%{busca}%")

                # Total count
                cursor.execute(f"SELECT COUNT(*) FROM fragmentos {where_clause}", params)
                total = cursor.fetchone()[0]

                # Fetch items
                cursor.execute(
                    f"""
                    SELECT id, resumo, importance_score, criado_em
                    FROM fragmentos
                    {where_clause}
                    ORDER BY criado_em DESC
                    LIMIT %s OFFSET %s
                    """,
                    params + [limit, offset],
                )

                columns = ["id", "resumo", "importance_score", "criado_em"]
                rows = cursor.fetchall()
                items = [dict(zip(columns, row)) for row in rows]

                # Convert datetime to ISO string
                for item in items:
                    if item["criado_em"]:
                        item["criado_em"] = item["criado_em"].isoformat()

                return jsonify({"items": items, "total": total}), 200

        except Exception as e:
            logger.error(f"❌ /dados/fragmentos error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    @app.route("/dados/fragmentos/<int:frag_id>", methods=["PATCH"])
    def patch_fragmento(frag_id):
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty body"}), 400

            novo_resumo = data.get("resumo", "").strip()
            if not novo_resumo:
                return jsonify({"error": "resumo is required"}), 400

            with get_connection() as conn:
                cursor = conn.cursor()

                # Validate ownership
                cursor.execute(
                    "SELECT id FROM fragmentos WHERE id = %s AND usuario_id = %s",
                    (frag_id, USUARIO_ID),
                )
                if not cursor.fetchone():
                    return jsonify({"error": "not_found"}), 404

                # Update
                cursor.execute(
                    "UPDATE fragmentos SET resumo = %s WHERE id = %s",
                    (novo_resumo, frag_id),
                )
                conn.commit()

                # Fetch updated
                cursor.execute(
                    "SELECT id, resumo, importance_score, criado_em FROM fragmentos WHERE id = %s",
                    (frag_id,),
                )
                row = cursor.fetchone()
                item = dict(
                    zip(["id", "resumo", "importance_score", "criado_em"], row)
                )
                if item["criado_em"]:
                    item["criado_em"] = item["criado_em"].isoformat()

                logger.info(f"✏️ Updated fragmento {frag_id}")
                return jsonify({"ok": True, "item": item}), 200

        except Exception as e:
            logger.error(f"❌ /dados/fragmentos PATCH error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    # ─────────────────────────────────────────────────────────────
    # ENTIDADES
    # ─────────────────────────────────────────────────────────────

    @app.route("/dados/entidades", methods=["GET"])
    def get_entidades():
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            tipo = request.args.get("tipo", "", type=str).strip()
            status = request.args.get("status", "", type=str).strip()
            busca = request.args.get("busca", "", type=str).strip()

            with get_connection() as conn:
                cursor = conn.cursor()

                where_clause = "WHERE usuario_id = %s AND status != 'deletado'"
                params = [USUARIO_ID]

                if tipo:
                    where_clause += " AND tipo = %s"
                    params.append(tipo)

                if status:
                    where_clause += " AND status = %s"
                    params.append(status)

                if busca:
                    where_clause += " AND nome ILIKE %s"
                    params.append(f"%{busca}%")

                # Total count
                cursor.execute(f"SELECT COUNT(*) FROM entidades {where_clause}", params)
                total = cursor.fetchone()[0]

                # Fetch items
                cursor.execute(
                    f"""
                    SELECT id, nome, nome_normalizado, tipo, descricao, status, criado_em
                    FROM entidades
                    {where_clause}
                    ORDER BY frequencia DESC, criado_em DESC
                    LIMIT 100
                    """,
                    params,
                )

                columns = ["id", "nome", "nome_normalizado", "tipo", "descricao", "status", "criado_em"]
                rows = cursor.fetchall()
                items = [dict(zip(columns, row)) for row in rows]

                for item in items:
                    if item["criado_em"]:
                        item["criado_em"] = item["criado_em"].isoformat()

                return jsonify({"items": items, "total": total}), 200

        except Exception as e:
            logger.error(f"❌ /dados/entidades error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    @app.route("/dados/entidades/<int:ent_id>", methods=["PATCH"])
    def patch_entidade(ent_id):
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty body"}), 400

            novo_nome = data.get("nome", "").strip()
            nova_descricao = data.get("descricao", "").strip()
            novo_status = data.get("status", "").strip()

            if not novo_nome:
                return jsonify({"error": "nome is required"}), 400

            with get_connection() as conn:
                cursor = conn.cursor()

                # Validate ownership
                cursor.execute(
                    "SELECT tipo FROM entidades WHERE id = %s AND usuario_id = %s",
                    (ent_id, USUARIO_ID),
                )
                row = cursor.fetchone()
                if not row:
                    return jsonify({"error": "not_found"}), 404

                tipo = row[0]

                # Prepare update
                update_fields = ["nome = %s"]
                params = [novo_nome]

                nome_normalizado = novo_nome.lower().strip()
                update_fields.append("nome_normalizado = %s")
                params.append(nome_normalizado)

                if nova_descricao:
                    update_fields.append("descricao = %s")
                    params.append(nova_descricao)

                if novo_status in ["ativo", "pendente", "ambiguo"]:
                    update_fields.append("status = %s")
                    params.append(novo_status)

                params.append(ent_id)

                # Execute update
                try:
                    cursor.execute(
                        f"UPDATE entidades SET {', '.join(update_fields)} WHERE id = %s",
                        params,
                    )
                    conn.commit()
                except Exception as db_error:
                    conn.rollback()
                    # Check if it's a unique constraint violation
                    if "idx_entidades_tipo_normalizado" in str(db_error):
                        return jsonify({
                            "error": "duplicate_name",
                            "message": f"Uma entidade com o nome '{novo_nome}' do tipo '{tipo}' já existe"
                        }), 409
                    raise

                # Fetch updated
                cursor.execute(
                    """SELECT id, nome, nome_normalizado, tipo, descricao, status, criado_em
                       FROM entidades WHERE id = %s""",
                    (ent_id,),
                )
                row = cursor.fetchone()
                item = dict(
                    zip(
                        ["id", "nome", "nome_normalizado", "tipo", "descricao", "status", "criado_em"],
                        row,
                    )
                )
                if item["criado_em"]:
                    item["criado_em"] = item["criado_em"].isoformat()

                logger.info(f"✏️ Updated entidade {ent_id}: {novo_nome}")
                return jsonify({"ok": True, "item": item}), 200

        except Exception as e:
            logger.error(f"❌ /dados/entidades PATCH error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    # ─────────────────────────────────────────────────────────────
    # TÓPICOS
    # ─────────────────────────────────────────────────────────────

    @app.route("/dados/topicos", methods=["GET"])
    def get_topicos():
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            busca = request.args.get("busca", "", type=str).strip()

            with get_connection() as conn:
                cursor = conn.cursor()

                where_clause = "WHERE usuario_id = %s AND status != 'deletado'"
                params = [USUARIO_ID]

                if busca:
                    where_clause += " AND caminho ILIKE %s"
                    params.append(f"%{busca}%")

                # Total count
                cursor.execute(f"SELECT COUNT(*) FROM topicos {where_clause}", params)
                total = cursor.fetchone()[0]

                # Fetch items
                cursor.execute(
                    f"""
                    SELECT id, caminho, nome, descricao, status, criado_em
                    FROM topicos
                    {where_clause}
                    ORDER BY frequencia DESC, criado_em DESC
                    LIMIT 100
                    """,
                    params,
                )

                columns = ["id", "caminho", "nome", "descricao", "status", "criado_em"]
                rows = cursor.fetchall()
                items = [dict(zip(columns, row)) for row in rows]

                for item in items:
                    if item["criado_em"]:
                        item["criado_em"] = item["criado_em"].isoformat()

                return jsonify({"items": items, "total": total}), 200

        except Exception as e:
            logger.error(f"❌ /dados/topicos error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    @app.route("/dados/topicos/<int:top_id>", methods=["PATCH"])
    def patch_topico(top_id):
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty body"}), 400

            novo_caminho = data.get("caminho", "").strip()
            nova_descricao = data.get("descricao", "").strip()

            if not novo_caminho:
                return jsonify({"error": "caminho is required"}), 400

            with get_connection() as conn:
                cursor = conn.cursor()

                # Validate ownership
                cursor.execute(
                    "SELECT id FROM topicos WHERE id = %s AND usuario_id = %s",
                    (top_id, USUARIO_ID),
                )
                if not cursor.fetchone():
                    return jsonify({"error": "not_found"}), 404

                # Extract nome from caminho (last part after " > ")
                nome = novo_caminho.split(" > ")[-1].strip()

                # Update
                cursor.execute(
                    """UPDATE topicos SET caminho = %s, nome = %s, descricao = %s WHERE id = %s""",
                    (novo_caminho, nome, nova_descricao, top_id),
                )
                conn.commit()

                # Fetch updated
                cursor.execute(
                    """SELECT id, caminho, nome, descricao, status, criado_em FROM topicos WHERE id = %s""",
                    (top_id,),
                )
                row = cursor.fetchone()
                item = dict(
                    zip(["id", "caminho", "nome", "descricao", "status", "criado_em"], row)
                )
                if item["criado_em"]:
                    item["criado_em"] = item["criado_em"].isoformat()

                logger.info(f"✏️ Updated topico {top_id}: {novo_caminho}")
                return jsonify({"ok": True, "item": item}), 200

        except Exception as e:
            logger.error(f"❌ /dados/topicos PATCH error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    # ─────────────────────────────────────────────────────────────
    # ACTION ITEMS (Tarefas)
    # ─────────────────────────────────────────────────────────────

    @app.route("/dados/action-items", methods=["GET"])
    def get_action_items():
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            status = request.args.get("status", "", type=str).strip()

            with get_connection() as conn:
                cursor = conn.cursor()

                where_clause = "WHERE usuario_id = %s"
                params = [USUARIO_ID]

                if status:
                    where_clause += " AND status = %s"
                    params.append(status)

                # Total count
                cursor.execute(
                    f"SELECT COUNT(*) FROM action_items {where_clause}", params
                )
                total = cursor.fetchone()[0]

                # Fetch items
                cursor.execute(
                    f"""
                    SELECT id, fragmento_id, texto, status, atualizado_por, criado_em
                    FROM action_items
                    {where_clause}
                    ORDER BY criado_em DESC
                    LIMIT 100
                    """,
                    params,
                )

                columns = ["id", "fragmento_id", "texto", "status", "atualizado_por", "criado_em"]
                rows = cursor.fetchall()
                items = [dict(zip(columns, row)) for row in rows]

                for item in items:
                    if item["criado_em"]:
                        item["criado_em"] = item["criado_em"].isoformat()

                return jsonify({"items": items, "total": total}), 200

        except Exception as e:
            logger.error(f"❌ /dados/action-items error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    @app.route("/dados/action-items/<int:task_id>", methods=["PATCH"])
    def patch_action_item(task_id):
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty body"}), 400

            novo_status = data.get("status", "").strip()
            novo_texto = data.get("texto", "").strip()

            with get_connection() as conn:
                cursor = conn.cursor()

                # Validate ownership
                cursor.execute(
                    """SELECT id FROM action_items
                       WHERE id = %s AND usuario_id = %s""",
                    (task_id, USUARIO_ID),
                )
                if not cursor.fetchone():
                    return jsonify({"error": "not_found"}), 404

                # Prepare update
                update_fields = []
                params = []

                if novo_status in ["pendente", "concluido", "cancelado"]:
                    update_fields.append("status = %s")
                    params.append(novo_status)

                if novo_texto:
                    update_fields.append("texto = %s")
                    params.append(novo_texto)

                if not update_fields:
                    return jsonify({"error": "no_updates_provided"}), 400

                update_fields.append("atualizado_por = %s")
                params.append("user")

                params.append(task_id)

                # Execute update
                cursor.execute(
                    f"""UPDATE action_items SET {', '.join(update_fields)},
                       criado_em = criado_em WHERE id = %s""",
                    params,
                )
                conn.commit()

                # Fetch updated
                cursor.execute(
                    """SELECT id, fragmento_id, texto, status, atualizado_por, criado_em
                       FROM action_items WHERE id = %s""",
                    (task_id,),
                )
                row = cursor.fetchone()
                item = dict(
                    zip(
                        ["id", "fragmento_id", "texto", "status", "atualizado_por", "criado_em"],
                        row,
                    )
                )
                if item["criado_em"]:
                    item["criado_em"] = item["criado_em"].isoformat()

                logger.info(f"✏️ Updated action_item {task_id}")
                return jsonify({"ok": True, "item": item}), 200

        except Exception as e:
            logger.error(f"❌ /dados/action-items PATCH error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    # ─────────────────────────────────────────────────────────────
    # SOFT DELETE — ENTIDADES e TÓPICOS
    # ─────────────────────────────────────────────────────────────

    @app.route("/dados/entidades/<int:ent_id>", methods=["DELETE"])
    def delete_entidade(ent_id):
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT nome FROM entidades WHERE id = %s AND usuario_id = %s",
                    (ent_id, USUARIO_ID),
                )
                row = cursor.fetchone()
                if not row:
                    return jsonify({"error": "not_found"}), 404

                nome = row[0]

                cursor.execute(
                    "UPDATE entidades SET status = 'deletado' WHERE id = %s",
                    (ent_id,),
                )
                conn.commit()

                logger.info(f"🗑 Soft-deleted entidade {ent_id}: {nome}")
                return jsonify({"ok": True}), 200

        except Exception as e:
            logger.error(f"❌ /dados/entidades DELETE error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    @app.route("/dados/topicos/<int:top_id>", methods=["DELETE"])
    def delete_topico(top_id):
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT caminho FROM topicos WHERE id = %s AND usuario_id = %s",
                    (top_id, USUARIO_ID),
                )
                row = cursor.fetchone()
                if not row:
                    return jsonify({"error": "not_found"}), 404

                caminho = row[0]

                cursor.execute(
                    "UPDATE topicos SET status = 'deletado' WHERE id = %s",
                    (top_id,),
                )
                conn.commit()

                logger.info(f"🗑 Soft-deleted topico {top_id}: {caminho}")
                return jsonify({"ok": True}), 200

        except Exception as e:
            logger.error(f"❌ /dados/topicos DELETE error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    # ─────────────────────────────────────────────────────────────
    # CORREÇÕES DE TEXTO
    # ─────────────────────────────────────────────────────────────

    @app.route("/dados/correcoes", methods=["GET"])
    def get_correcoes():
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """SELECT id, texto_errado, texto_correto, criado_em
                       FROM correcoes_texto
                       WHERE usuario_id = %s
                       ORDER BY criado_em DESC""",
                    (USUARIO_ID,),
                )
                columns = ["id", "texto_errado", "texto_correto", "criado_em"]
                rows = cursor.fetchall()
                items = [dict(zip(columns, row)) for row in rows]

                for item in items:
                    if item["criado_em"]:
                        item["criado_em"] = item["criado_em"].isoformat()

                return jsonify({"items": items, "total": len(items)}), 200

        except Exception as e:
            logger.error(f"❌ /dados/correcoes GET error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    @app.route("/dados/correcoes", methods=["POST"])
    def post_correcao():
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty body"}), 400

            texto_errado = data.get("texto_errado", "").strip()
            texto_correto = data.get("texto_correto", "").strip()

            if not texto_errado or not texto_correto:
                return jsonify({"error": "texto_errado e texto_correto são obrigatórios"}), 400

            if texto_errado == texto_correto:
                return jsonify({"error": "texto_errado e texto_correto não podem ser iguais"}), 400

            with get_connection() as conn:
                cursor = conn.cursor()

                try:
                    cursor.execute(
                        """INSERT INTO correcoes_texto (texto_errado, texto_correto, usuario_id)
                           VALUES (%s, %s, %s)
                           RETURNING id, texto_errado, texto_correto, criado_em""",
                        (texto_errado, texto_correto, USUARIO_ID),
                    )
                    conn.commit()
                except Exception as db_error:
                    conn.rollback()
                    if "unique" in str(db_error).lower():
                        return jsonify({
                            "error": "duplicate",
                            "message": f"Já existe uma correção para '{texto_errado}'"
                        }), 409
                    raise

                row = cursor.fetchone()
                item = dict(zip(["id", "texto_errado", "texto_correto", "criado_em"], row))
                if item["criado_em"]:
                    item["criado_em"] = item["criado_em"].isoformat()

                logger.info(f"➕ Added correção: '{texto_errado}' → '{texto_correto}'")
                return jsonify({"ok": True, "item": item}), 201

        except Exception as e:
            logger.error(f"❌ /dados/correcoes POST error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    @app.route("/dados/correcoes/<int:corr_id>", methods=["DELETE"])
    def delete_correcao(corr_id):
        if not _check_auth():
            return jsonify({"error": "unauthorized"}), 401

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT texto_errado FROM correcoes_texto WHERE id = %s AND usuario_id = %s",
                    (corr_id, USUARIO_ID),
                )
                row = cursor.fetchone()
                if not row:
                    return jsonify({"error": "not_found"}), 404

                cursor.execute("DELETE FROM correcoes_texto WHERE id = %s", (corr_id,))
                conn.commit()

                logger.info(f"🗑 Deleted correção {corr_id}: '{row[0]}'")
                return jsonify({"ok": True}), 200

        except Exception as e:
            logger.error(f"❌ /dados/correcoes DELETE error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500
