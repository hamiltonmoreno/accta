"""Cobertura IDOR — SC-001 (spec 019, WS-C).

Prova, regeneravel em runtime, que TODA a rota que recebe um parametro de caminho
esta classificada numa classe de acesso (SC-001 = 100%), e que toda a rota
owner/parent_scoped tem prova comportamental «B nao toca no objeto de A» — via
teste real (test_idor.py) OU citacao estrutural especifica (o gate em AUDIT).

O denominador (rotas com {param}) e enumerado do app EM RUNTIME → nunca fica
stale. Uma rota nova sem entrada em AUDIT deixa test_every_id_route_classified
VERMELHO ate ser classificada (obriga o autor a decidir a classe = SC-008).

Classes: public / authenticated / role / owner / parent_scoped (ver data-model.md).
"""
from __future__ import annotations

import re

import pytest

from server import app

pytestmark = pytest.mark.unit

ACCESS_CLASSES = {"public", "authenticated", "role", "owner", "parent_scoped"}

# (method, path) -> (access_class, gate). Levantamento endpoint-a-endpoint (spec 019).
# Uma rota = uma classe, com citacao do gate real. NAO editar sem rever o handler.
AUDIT: dict[tuple[str, str], tuple[str, str]] = {
    ('DELETE', '/api/admin/custom-roles/{role_id}'): ('role', '_require_admin(current_user) -> is_admin(current_user)'),
    ('DELETE', '/api/admin/invite/{user_id}'): ('role', 'if not is_admin(current_user): 403'),
    ('DELETE', '/api/assembleias/{assembleia_id}/palavra/{qid}'): ('owner', 'retirar_palavra: p["user_id"] == current_user.id OR can_convene_assembleia(current_user) (owner-or-staff)'),
    ('DELETE', '/api/benefits/{benefit_id}'): ('role', 'has_role_or_privilege(manage_benefits)'),
    ('DELETE', '/api/comunicados/{comunicado_id}'): ('owner', '_assert_owner_or_admin (created_by==user OR is_admin)'),
    ('DELETE', '/api/defesa-profissional/{defesa_id}'): ('role', '_can_manage (Direcao/admin)'),
    ('DELETE', '/api/events/{event_id}'): ('role', 'has_role_or_privilege(manage_events)'),
    ('DELETE', '/api/events/{event_id}/expenses/{tx_id}'): ('parent_scoped', '_require_manage_events + tx re-query {id,event_id,type}'),
    ('DELETE', '/api/events/{event_id}/receitas/{tx_id}'): ('parent_scoped', '_require_manage_events + tx re-query {id,event_id,type}'),
    ('DELETE', '/api/events/{event_id}/register'): ('authenticated', 'self-unregister (current_user.id)'),
    ('DELETE', '/api/finances/transactions/{transaction_id}'): ('role', 'require_manage_finances'),
    ('DELETE', '/api/formacoes/{formacao_id}'): ('role', '_can_manage (Direcao/admin)'),
    ('DELETE', '/api/gallery/albums/{album_id}'): ('role', 'has_role_or_privilege(moderate_content)'),
    ('DELETE', '/api/gallery/photos/{photo_id}'): ('owner', 'is_staff(moderate_content) OR photo.uploaded_by==current_user.id'),
    ('DELETE', '/api/notifications/{notification_id}'): ('owner', 'delete_one scoped {id, user_id==current_user.id}'),
    ('DELETE', '/api/peticoes/{peticao_id}/assinar'): ('owner', "retirar_assinatura: delete_one({peticao_id, user_id: current_user.id}) â€” scoped to caller's own signature"),
    ('DELETE', '/api/posts/{post_id}'): ('role', 'has_role_or_privilege(moderate_content)'),
    ('DELETE', '/api/projects/{project_id}'): ('role', 'is_admin(current_user) else 403 (no ownership branch)'),
    ('DELETE', '/api/projects/{project_id}/comments/{comment_id}'): ('owner', "comment fetched scoped by project_id; comment['user_id']==current_user.id (OR is_admin)"),
    ('DELETE', '/api/projects/{project_id}/expenses/{expense_id}'): ('parent_scoped', 'can_manage_project gate on parent; tx find_one scoped by {id, project_id, type=despesa}, no child-ownership comparison'),
    ('DELETE', '/api/projects/{project_id}/milestones/{milestone_id}'): ('parent_scoped', 'can_manage_project gate on parent; delete_one scoped by {id, project_id}, no child-ownership comparison'),
    ('DELETE', '/api/projects/{project_id}/tasks/{task_id}'): ('parent_scoped', 'can_manage_project gate on parent; delete_one scoped by {id, project_id}, no child-ownership comparison'),
    ('DELETE', '/api/publicacoes/{publicacao_id}'): ('role', '_can_manage (Direcao/admin)'),
    ('DELETE', '/api/relacoes-externas/{relacao_id}'): ('role', '_can_manage (Direcao/admin)'),
    ('DELETE', '/api/upload/{category}/{filename}'): ('role', 'is_admin'),
    ('DELETE', '/api/users/{user_id}'): ('role', "if not has_role_or_privilege(current_user, ('admin',), 'manage_users'): 403 (user_id==current_user.id only DENIES self-delete, not an ownership grant)"),
    ('DELETE', '/api/users/{user_id}/photo'): ('role', "if not module_gate(current_user, 'users_photo_moderation'): 403"),
    ('DELETE', '/api/wall/{post_id}'): ('owner', 'post.user_id==current_user.id OR moderate_content'),
    ('DELETE', '/api/wall/{post_id}/comments/{comment_id}'): ('owner', 'comment.user_id==current_user.id OR moderate_content'),
    ('GET', '/api/assembleias/{assembleia_id}'): ('authenticated', 'get_assembleia: Depends(get_current_user) only; can_convene branch merely redacts check_in_code fields'),
    ('GET', '/api/assembleias/{assembleia_id}/convidados'): ('role', 'list_convidados: _require_convene (can_convene_assembleia)'),
    ('GET', '/api/assembleias/{assembleia_id}/deliberacoes'): ('authenticated', 'list_deliberacoes: get_current_user; collection listed by assembleia_id, no per-user gate'),
    ('GET', '/api/assembleias/{assembleia_id}/deliberacoes/{did}'): ('parent_scoped', 'get_deliberacao: no role gate; _get_deliberacao fetches {id: did, assembleia_id} (child scoped by parent id)'),
    ('GET', '/api/assembleias/{assembleia_id}/documentos'): ('authenticated', 'list_documentos: get_current_user only'),
    ('GET', '/api/assembleias/{assembleia_id}/expediente'): ('authenticated', 'list_expediente: get_current_user only'),
    ('GET', '/api/assembleias/{assembleia_id}/mocoes'): ('authenticated', 'list_mocoes: get_current_user only'),
    ('GET', '/api/assembleias/{assembleia_id}/palavra'): ('authenticated', 'list_palavra: get_current_user only'),
    ('GET', '/api/assembleias/{assembleia_id}/presencas'): ('role', 'list_presencas: _require_convene (can_convene_assembleia)'),
    ('GET', '/api/assembleias/{assembleia_id}/quorum'): ('authenticated', 'get_quorum: get_current_user only'),
    ('GET', '/api/assembleias/{assembleia_id}/stream'): ('authenticated', 'assembleia_stream: _extract_token + get_user_from_token (401 if missing/invalid); any authenticated member'),
    ('GET', '/api/atos/{ato_id}'): ('role', '_require_view (can_view_finances OR is_direcao)'),
    ('GET', '/api/balancetes/{balancete_id}'): ('role', '_require_view_finances(current_user) -> can_view_finances; find_one by top-level id, no parent scoping'),
    ('GET', '/api/comunicados/{comunicado_id}'): ('role', '_guard (_can_send)'),
    ('GET', '/api/defesa-profissional/{defesa_id}'): ('owner', '_can_manage(Direcao/admin) OR defesa.created_by==user'),
    ('GET', '/api/documents/public/{document_id}/download'): ('public', 'visibility=publico, no auth'),
    ('GET', '/api/documents/{document_id}/download'): ('authenticated', 'ensure_can_access_document (visibility; restrito=manage_documents)'),
    ('GET', '/api/eleicoes/{eleicao_id}'): ('authenticated', 'get_current_user only; _get_eleicao fetches by id, no role/ownership branch'),
    ('GET', '/api/eleicoes/{eleicao_id}/listas'): ('authenticated', 'get_current_user only; lists all listas filtered by eleicao_id (collection, no child_id, no capability/ownership gate)'),
    ('GET', '/api/esclarecimentos/{esc_id}'): ('owner', "obter_esclarecimento: 403 unless e.created_by == current_user.id OR _can_answer_orgao(user, orgao) â€” ownership comparison OR'd with role branch"),
    ('GET', '/api/events/{event_id}'): ('authenticated', 'ensure_can_access_event: visibility gate, nao ownership'),
    ('GET', '/api/events/{event_id}/attendees'): ('owner', 'manage_events OR current_user.id==event.created_by'),
    ('GET', '/api/events/{event_id}/expenses'): ('authenticated', 'ensure_can_view_event (visibility)'),
    ('GET', '/api/events/{event_id}/receitas'): ('authenticated', 'ensure_can_view_event (visibility)'),
    ('GET', '/api/exercicios/{ano}'): ('role', '_require_view_finances(current_user) -> can_view_finances; ano is top-level PK, no ownership/parent scoping'),
    ('GET', '/api/exercicios/{ano}/orcamento/execucao'): ('role', '_require_view_finances(current_user) -> can_view_finances'),
    ('GET', '/api/exercicios/{ano}/relatorio/pdf'): ('role', '_require_view_finances(current_user) -> can_view_finances'),
    ('GET', '/api/finances/transactions/{transaction_id}/proof'): ('role', 'require_view_finances (WS-A: proof gated)'),
    ('GET', '/api/formacoes/{formacao_id}'): ('authenticated', 'get_current_user only (route-protect)'),
    ('GET', '/api/gallery/albums/{album_id}'): ('authenticated', 'get_current_user only'),
    ('GET', '/api/honorarios/{nom_id}'): ('role', 'obter_honorario: if not _can_see_honorarios(current_user) -> 403 (DirecÃ§Ã£o/Mesa AG/admin)'),
    ('GET', '/api/peticoes/{peticao_id}'): ('authenticated', 'obter_peticao: only Depends(get_current_user); returns _peticao_view for any petition â€” no ownership or role branch'),
    ('GET', '/api/polls/{poll_id}/results'): ('authenticated', "results apos 'encerrada'; admin anytime; nao ownership"),
    ('GET', '/api/posts/{id_or_slug}'): ('public', 'get_optional_user; published unless staff'),
    ('GET', '/api/projects/{project_id}'): ('owner', 'can_view_project: created_by==user.id OR responsible_id==user.id (OR public+published, OR is_admin)'),
    ('GET', '/api/projects/{project_id}/expenses'): ('owner', 'can_view_project: created_by==user.id OR responsible_id==user.id (OR public+published, OR is_admin)'),
    ('GET', '/api/propostas-ag/{proposta_id}'): ('owner', 'obter_proposta: 403 unless _can_triage_propostas OR pr.created_by == current_user.id OR status in _PROPOSTA_PUBLICAS â€” ownership comparison present'),
    ('GET', '/api/public/defesa-profissional/{defesa_id}'): ('public', 'status=publicado & visibility=publico, no auth'),
    ('GET', '/api/public/publicacoes/{publicacao_id}'): ('public', 'visibility=publico, no auth'),
    ('GET', '/api/publicacoes/{publicacao_id}'): ('authenticated', "get_current_user; created_by so define flag 'autor'"),
    ('GET', '/api/reclamacoes/{rec_id}'): ('owner', "obter_reclamacao: if not _can_see_reclamacao -> 403 (r.created_by == user.id OR admin OR is_direcao) â€” ownership comparison OR'd with role branch"),
    ('GET', '/api/regulamentos/{regulamento_id}'): ('role', "_can_manage(current_user) branches visibility (non-managers only see 'aprovado' versions, else 404); top-level find_one, no ownership/parent scoping"),
    ('GET', '/api/relacoes-externas/{relacao_id}'): ('authenticated', 'get_current_user only (route-protect)'),
    ('GET', '/api/sancoes/{sancao_id}'): ('owner', 'current_user.id==s.user_id OR _require_disciplina(Direcao/admin)'),
    ('GET', '/api/users/{user_id}'): ('owner', "is_self = current_user.id == user_id OR has_role_or_privilege(('admin',),'manage_users'); self gets sensitive-PII projection, others 403"),
    ('GET', '/api/users/{user_id}/cargo-history'): ('owner', "if not (current_user.id == user_id or has_role_or_privilege(('admin',),'manage_users')): 403"),
    ('GET', '/api/users/{user_id}/sancoes'): ('owner', 'is_self = current_user.id == user_id; if not (is_self or is_admin/is_direcao): 403 (non-privileged self gets _redact)'),
    ('GET', '/api/validate/{qr_hash}'): ('public', 'no get_current_user (public QR validator)'),
    ('GET', '/api/wall/{post_id}/comments'): ('authenticated', 'get_current_user; staff tambem ve pending'),
    ('PATCH', '/api/admin/custom-roles/{role_id}'): ('role', '_require_admin(current_user) -> is_admin(current_user)'),
    ('PATCH', '/api/benefits/{benefit_id}'): ('role', 'has_role_or_privilege(manage_benefits)'),
    ('PATCH', '/api/comunicados/{comunicado_id}'): ('owner', '_assert_owner_or_admin (created_by==user OR is_admin)'),
    ('PATCH', '/api/defesa-profissional/{defesa_id}'): ('role', '_can_manage (Direcao/admin)'),
    ('PATCH', '/api/events/{event_id}'): ('role', 'has_role_or_privilege(manage_events)'),
    ('PATCH', '/api/finances/transactions/{transaction_id}'): ('role', 'require_manage_finances'),
    ('PATCH', '/api/formacoes/{formacao_id}'): ('role', '_can_manage (Direcao/admin)'),
    ('PATCH', '/api/gallery/albums/{album_id}'): ('role', 'has_role_or_privilege(moderate_content)'),
    ('PATCH', '/api/gallery/photos/{photo_id}/approve'): ('role', 'has_role_or_privilege(moderate_content)'),
    ('PATCH', '/api/gallery/photos/{photo_id}/reject'): ('role', 'has_role_or_privilege(moderate_content)'),
    ('PATCH', '/api/notifications/{notification_id}/read'): ('owner', 'update_one scoped {id, user_id==current_user.id}'),
    ('PATCH', '/api/polls/{poll_id}/status'): ('role', 'is_admin'),
    ('PATCH', '/api/posts/{post_id}'): ('role', 'has_role_or_privilege(moderate_content)'),
    ('PATCH', '/api/projects/{project_id}'): ('owner', 'can_manage_project: created_by==user.id OR responsible_id==user.id (OR is_admin)'),
    ('PATCH', '/api/projects/{project_id}/approve'): ('role', 'is_admin(current_user) else 403 (no ownership branch)'),
    ('PATCH', '/api/projects/{project_id}/milestones/{milestone_id}'): ('parent_scoped', 'can_manage_project gate on parent; milestone find_one scoped by {id, project_id}, no child-ownership comparison'),
    ('PATCH', '/api/projects/{project_id}/tasks/{task_id}'): ('owner', 'task fetched scoped by project_id; is_assignee = task.assignee_id==current_user.id OR is_manager=can_manage_project'),
    ('PATCH', '/api/publicacoes/{publicacao_id}'): ('role', '_can_manage (Direcao/admin)'),
    ('PATCH', '/api/relacoes-externas/{relacao_id}'): ('role', '_can_manage (Direcao/admin)'),
    ('PATCH', '/api/users/{user_id}'): ('role', "if not has_role_or_privilege(current_user, ('admin',), 'manage_users'): 403 (role/privileges/custom_role_id writes further require is_admin)"),
    ('PATCH', '/api/users/{user_id}/status'): ('role', "if not has_role_or_privilege(current_user, ('admin',), 'manage_users'): 403"),
    ('PATCH', '/api/wall/{post_id}/approve'): ('role', 'has_role_or_privilege(moderate_content)'),
    ('PATCH', '/api/wall/{post_id}/like'): ('authenticated', 'socio ativo toggle like'),
    ('PATCH', '/api/wall/{post_id}/pin'): ('role', 'has_role_or_privilege(moderate_content)'),
    ('POST', '/api/admin/registration-requests/{user_id}/approve'): ('role', 'if not is_admin(current_user): 403'),
    ('POST', '/api/admin/registration-requests/{user_id}/reject'): ('role', 'if not is_admin(current_user): 403'),
    ('POST', '/api/admin/users/{user_id}/demote'): ('role', '_require_cargo_admin(current_user) -> is_admin(current_user)'),
    ('POST', '/api/admin/users/{user_id}/promote'): ('role', '_require_cargo_admin(current_user) -> is_admin(current_user)'),
    ('POST', '/api/assembleias/{assembleia_id}/checkin'): ('authenticated', 'self_checkin: get_current_user; self-action for current_user.id, member-only, no role/ownership on existing object'),
    ('POST', '/api/assembleias/{assembleia_id}/checkin/abrir'): ('role', 'abrir_checkin: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/assembleias/{assembleia_id}/checkin/fechar'): ('role', 'fechar_checkin: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/assembleias/{assembleia_id}/checkin/scan'): ('role', 'checkin_scan: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/assembleias/{assembleia_id}/convidados'): ('role', 'adicionar_convidado: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/assembleias/{assembleia_id}/convidados/{cid}/checkin'): ('role', 'checkin_convidado: _require_convene (unconditional; convidado also fetched scoped {id: cid, assembleia_id})'),
    ('POST', '/api/assembleias/{assembleia_id}/deliberacoes'): ('role', 'register_deliberacao: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/assembleias/{assembleia_id}/deliberacoes/abrir'): ('role', 'abrir_deliberacao: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/assembleias/{assembleia_id}/deliberacoes/{did}/apurar'): ('role', 'apurar_deliberacao: _require_convene (unconditional Mesa/admin gate; _get_deliberacao scoped fetch is data-integrity)'),
    ('POST', '/api/assembleias/{assembleia_id}/deliberacoes/{did}/registar-contagem'): ('role', 'registar_contagem: _require_convene (unconditional; _get_deliberacao scoped fetch is data-integrity)'),
    ('POST', '/api/assembleias/{assembleia_id}/deliberacoes/{did}/votar'): ('parent_scoped', 'votar_deliberacao: no role gate; _get_deliberacao {id: did, assembleia_id} (child scoped by parent) + must be present & can_vote'),
    ('POST', '/api/assembleias/{assembleia_id}/documentos'): ('role', 'anexar_documento: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/assembleias/{assembleia_id}/encerrar'): ('role', 'encerrar_assembleia: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/assembleias/{assembleia_id}/expediente'): ('role', 'registar_expediente: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/assembleias/{assembleia_id}/fase'): ('role', 'transicao_fase: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/assembleias/{assembleia_id}/mocoes'): ('authenticated', 'submeter_mocao: get_current_user + _is_present(current_user.id) eligibility; any present member'),
    ('POST', '/api/assembleias/{assembleia_id}/mocoes/{mid}/colocar-a-voto'): ('role', 'colocar_mocao_a_voto: _require_convene (unconditional; _get_mocao scoped fetch is data-integrity)'),
    ('POST', '/api/assembleias/{assembleia_id}/mocoes/{mid}/retirar'): ('owner', 'retirar_mocao: m["proposta_por"] == current_user.id OR can_convene_assembleia(current_user) (owner-or-staff)'),
    ('POST', '/api/assembleias/{assembleia_id}/palavra'): ('authenticated', 'pedir_palavra: get_current_user + _is_present(current_user.id) eligibility; any present member'),
    ('POST', '/api/assembleias/{assembleia_id}/palavra/convidado'): ('role', 'pedir_palavra_convidado: _require_convene (convidado_id from body validated against assembleia_id)'),
    ('POST', '/api/assembleias/{assembleia_id}/palavra/{qid}/iniciar'): ('role', 'iniciar_palavra: _require_convene (unconditional; _get_palavra scoped fetch is data-integrity)'),
    ('POST', '/api/assembleias/{assembleia_id}/palavra/{qid}/ordenar'): ('role', 'ordenar_palavra: _require_convene (unconditional; _get_palavra scoped fetch is data-integrity)'),
    ('POST', '/api/assembleias/{assembleia_id}/palavra/{qid}/terminar'): ('role', 'terminar_palavra: _require_convene (unconditional; _get_palavra scoped fetch is data-integrity)'),
    ('POST', '/api/assembleias/{assembleia_id}/presencas'): ('role', 'register_presenca: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/assembleias/{assembleia_id}/segunda-convocatoria'): ('role', 'segunda_convocatoria: _require_convene (can_convene_assembleia)'),
    ('POST', '/api/atos/{ato_id}/assinar'): ('role', '_require_sign (is_direcao)'),
    ('POST', '/api/atos/{ato_id}/cancelar'): ('owner', 'is_admin OR ato.created_by==current_user.id'),
    ('POST', '/api/atos/{ato_id}/executar'): ('role', '_require_execute (is_admin OR is_tesoureiro)'),
    ('POST', '/api/balancetes/{balancete_id}/auditar'): ('role', '_require_cf(current_user) -> can_emit_parecer_cf; balancete fetched by top-level id'),
    ('POST', '/api/benefits/{benefit_id}/validate'): ('authenticated', 'socio ativo valida'),
    ('POST', '/api/comunicados/{comunicado_id}/enviar'): ('owner', '_assert_owner_or_admin (created_by==user OR is_admin)'),
    ('POST', '/api/defesa-profissional/{defesa_id}/aprovar'): ('role', '_can_manage (+ nao self)'),
    ('POST', '/api/defesa-profissional/{defesa_id}/arquivar'): ('role', '_can_manage'),
    ('POST', '/api/defesa-profissional/{defesa_id}/rejeitar'): ('role', '_can_manage (+ nao self)'),
    ('POST', '/api/defesa-profissional/{defesa_id}/submeter'): ('owner', 'defesa.created_by==user OR _can_manage'),
    ('POST', '/api/documents/{document_id}/access'): ('authenticated', 'ensure_can_access_document'),
    ('POST', '/api/eleicoes/{eleicao_id}/abrir-votacao'): ('role', '_require_manage(current_user, eleicao) = is_admin OR is_mesa_ag OR _is_comissao'),
    ('POST', '/api/eleicoes/{eleicao_id}/apurar'): ('role', '_require_manage(current_user, eleicao) = is_admin OR is_mesa_ag OR _is_comissao'),
    ('POST', '/api/eleicoes/{eleicao_id}/listas'): ('authenticated', 'get_current_user only; no caller role/ownership check (only status==candidaturas + candidate eligibility validated)'),
    ('POST', '/api/eleicoes/{eleicao_id}/listas/{lista_id}/validar'): ('parent_scoped', '_require_manage capability + lista re-fetched scoped by {"id": lista_id, "eleicao_id": eleicao_id} (404 if not in this election)'),
    ('POST', '/api/eleicoes/{eleicao_id}/proclamar'): ('role', 'is_admin(current_user) or is_mesa_ag(current_user)'),
    ('POST', '/api/eleicoes/{eleicao_id}/votar'): ('role', 'is_voting_member(current_user) (votes as self; voter_hash derived from current_user.id)'),
    ('POST', '/api/eleicoes/{eleicao_id}/voto-correspondencia'): ('role', '_require_manage(current_user, eleicao); registers vote for body user_id (validated is_voting_member)'),
    ('POST', '/api/esclarecimentos/{esc_id}/responder'): ('role', 'responder_esclarecimento: if not _can_answer_orgao(current_user, orgao_destino) -> 403 (admin OR Ã³rgÃ£o destinatÃ¡rio via _ORGAO_CHECK); no ownership branch'),
    ('POST', '/api/events/{event_id}/expenses'): ('role', '_require_manage_events'),
    ('POST', '/api/events/{event_id}/receitas'): ('role', '_require_manage_events'),
    ('POST', '/api/events/{event_id}/register'): ('authenticated', 'socio ativo self-register (current_user.id)'),
    ('POST', '/api/exercicios/{ano}/aprovar'): ('role', '_require_mesa_ag(current_user) -> is_admin or is_mesa_ag'),
    ('POST', '/api/exercicios/{ano}/orcamento'): ('role', '_require_direcao(current_user) -> is_admin or is_direcao'),
    ('POST', '/api/exercicios/{ano}/parecer'): ('role', '_require_cf(current_user) -> can_emit_parecer_cf'),
    ('POST', '/api/exercicios/{ano}/plano'): ('role', '_require_direcao(current_user) -> is_admin or is_direcao'),
    ('POST', '/api/exercicios/{ano}/reabrir'): ('role', '_require_mesa_ag(current_user) -> is_admin or is_mesa_ag'),
    ('POST', '/api/exercicios/{ano}/relatorio'): ('role', '_require_direcao(current_user) -> is_admin or is_direcao'),
    ('POST', '/api/exercicios/{ano}/submeter-ag'): ('role', '_require_mesa_ag(current_user) -> is_admin or is_mesa_ag'),
    ('POST', '/api/honorarios/{nom_id}/abrir-votacao'): ('role', 'abrir_votacao_honorario: if not _can_manage_honorarios(current_user) -> 403 (Mesa AG or admin)'),
    ('POST', '/api/honorarios/{nom_id}/apurar'): ('role', 'apurar_honorario: if not _can_manage_honorarios(current_user) -> 403 (Mesa AG or admin)'),
    ('POST', '/api/honorarios/{nom_id}/ligar-assembleia'): ('role', 'ligar_honorario_assembleia: if not _can_manage_honorarios(current_user) -> 403 (Mesa AG or admin)'),
    ('POST', '/api/peticoes/{peticao_id}/assinar'): ('role', "assinar_peticao: if not is_voting_member(current_user) -> 403 (voting-member capability); inserts caller's own signature"),
    ('POST', '/api/peticoes/{peticao_id}/encaminhar'): ('role', 'encaminhar_peticao: if not (is_admin(current_user) or is_mesa_ag(current_user)) -> 403'),
    ('POST', '/api/projects/{project_id}/comments'): ('owner', 'can_view_project: created_by==user.id OR responsible_id==user.id (OR public+published, OR is_admin)'),
    ('POST', '/api/projects/{project_id}/expenses'): ('owner', 'can_manage_project: created_by==user.id OR responsible_id==user.id (OR is_admin)'),
    ('POST', '/api/projects/{project_id}/milestones'): ('owner', 'can_manage_project: created_by==user.id OR responsible_id==user.id (OR is_admin); create gated by parent ownership, no child re-query'),
    ('POST', '/api/projects/{project_id}/tasks'): ('owner', 'can_manage_project: created_by==user.id OR responsible_id==user.id (OR is_admin); create gated by parent ownership'),
    ('POST', '/api/propostas-ag/{proposta_id}/incluir'): ('role', 'incluir_proposta: if not (is_admin(current_user) or is_mesa_ag(current_user)) -> 403'),
    ('POST', '/api/propostas-ag/{proposta_id}/triagem'): ('role', 'triar_proposta: if not _can_triage_propostas(current_user) -> 403 (admin/Mesa AG/DirecÃ§Ã£o)'),
    ('POST', '/api/reclamacoes/{rec_id}/decidir-recurso'): ('role', 'decidir_recurso: if not (is_admin(current_user) or is_mesa_ag(current_user)) -> 403'),
    ('POST', '/api/reclamacoes/{rec_id}/recurso'): ('owner', "abrir_recurso: if r.created_by != current_user.id -> 403 'Apenas o autor pode recorrer' (pure ownership)"),
    ('POST', '/api/reclamacoes/{rec_id}/responder'): ('role', 'responder_reclamacao: if not (is_admin(current_user) or is_direcao(current_user)) -> 403'),
    ('POST', '/api/regulamentos/{regulamento_id}/versoes'): ('role', '_require_manage(current_user) -> is_admin/is_direcao/manage_documents; validates parent then creates new versao (no existing-child re-query)'),
    ('POST', '/api/regulamentos/{regulamento_id}/versoes/{versao_id}/aprovar'): ('parent_scoped', '_get_versao(regulamento_id, versao_id) re-queries child filtered by regulamento_id (parent gates child); role branch also present (competencia: is_admin/is_mesa_ag for AG, else _require_manage)'),
    ('POST', '/api/regulamentos/{regulamento_id}/versoes/{versao_id}/revogar'): ('parent_scoped', '_get_versao(regulamento_id, versao_id) re-queries child filtered by regulamento_id (parent gates child); _require_manage also present'),
    ('POST', '/api/regulamentos/{regulamento_id}/versoes/{versao_id}/submeter'): ('parent_scoped', '_get_versao(regulamento_id, versao_id) re-queries child filtered by regulamento_id (parent gates child); _require_manage also present'),
    ('POST', '/api/sancoes/{sancao_id}/aplicar'): ('role', '_require_disciplina'),
    ('POST', '/api/sancoes/{sancao_id}/comissao'): ('role', '_require_disciplina'),
    ('POST', '/api/sancoes/{sancao_id}/decidir'): ('role', '_require_disciplina'),
    ('POST', '/api/sancoes/{sancao_id}/recurso'): ('owner', 'so o visado: current_user.id==s.user_id'),
    ('POST', '/api/upload/{category}'): ('role', 'per-category: is_admin (documents/logos) / moderate_content (banners/brand/covers)'),
    ('POST', '/api/wall/{post_id}/comments'): ('authenticated', 'socio ativo; approved-post check'),
    ('PUT', '/api/banners/{key}'): ('role', '_require_manager (moderate_content)'),
}

# owner/parent_scoped com negativo comportamental real (test_idor.py).
BEHAVIORAL_TESTED: set[tuple[str, str]] = {
    ('DELETE', '/api/gallery/photos/{photo_id}'),
    ('DELETE', '/api/notifications/{notification_id}'),
    ('DELETE', '/api/projects/{project_id}/comments/{comment_id}'),
    ('DELETE', '/api/projects/{project_id}/expenses/{expense_id}'),
    ('DELETE', '/api/projects/{project_id}/milestones/{milestone_id}'),
    ('DELETE', '/api/wall/{post_id}'),
    ('DELETE', '/api/wall/{post_id}/comments/{comment_id}'),
    ('GET', '/api/sancoes/{sancao_id}'),
    ('PATCH', '/api/notifications/{notification_id}/read'),
    ('PATCH', '/api/projects/{project_id}/milestones/{milestone_id}'),
    ('POST', '/api/atos/{ato_id}/cancelar'),
    ('POST', '/api/sancoes/{sancao_id}/recurso'),
}

# owner/parent_scoped cuja protecao e ESTRUTURAL — a citacao e o gate em AUDIT
# (owner-check helper OU filtro parent-scoped re-consultado pelo id do pai). Lista
# explicita (anti rubber-stamp): acrescentar aqui obriga a rever o gate no handler.
BEHAVIORAL_CITED: set[tuple[str, str]] = {
    ('DELETE', '/api/assembleias/{assembleia_id}/palavra/{qid}'),
    ('DELETE', '/api/comunicados/{comunicado_id}'),
    ('DELETE', '/api/events/{event_id}/expenses/{tx_id}'),
    ('DELETE', '/api/events/{event_id}/receitas/{tx_id}'),
    ('DELETE', '/api/peticoes/{peticao_id}/assinar'),
    ('DELETE', '/api/projects/{project_id}/tasks/{task_id}'),
    ('GET', '/api/assembleias/{assembleia_id}/deliberacoes/{did}'),
    ('GET', '/api/defesa-profissional/{defesa_id}'),
    ('GET', '/api/esclarecimentos/{esc_id}'),
    ('GET', '/api/events/{event_id}/attendees'),
    ('GET', '/api/projects/{project_id}'),
    ('GET', '/api/projects/{project_id}/expenses'),
    ('GET', '/api/propostas-ag/{proposta_id}'),
    ('GET', '/api/reclamacoes/{rec_id}'),
    ('GET', '/api/users/{user_id}'),
    ('GET', '/api/users/{user_id}/cargo-history'),
    ('GET', '/api/users/{user_id}/sancoes'),
    ('PATCH', '/api/comunicados/{comunicado_id}'),
    ('PATCH', '/api/projects/{project_id}'),
    ('PATCH', '/api/projects/{project_id}/tasks/{task_id}'),
    ('POST', '/api/assembleias/{assembleia_id}/deliberacoes/{did}/votar'),
    ('POST', '/api/assembleias/{assembleia_id}/mocoes/{mid}/retirar'),
    ('POST', '/api/comunicados/{comunicado_id}/enviar'),
    ('POST', '/api/defesa-profissional/{defesa_id}/submeter'),
    ('POST', '/api/eleicoes/{eleicao_id}/listas/{lista_id}/validar'),
    ('POST', '/api/projects/{project_id}/comments'),
    ('POST', '/api/projects/{project_id}/expenses'),
    ('POST', '/api/projects/{project_id}/milestones'),
    ('POST', '/api/projects/{project_id}/tasks'),
    ('POST', '/api/reclamacoes/{rec_id}/recurso'),
    ('POST', '/api/regulamentos/{regulamento_id}/versoes/{versao_id}/aprovar'),
    ('POST', '/api/regulamentos/{regulamento_id}/versoes/{versao_id}/revogar'),
    ('POST', '/api/regulamentos/{regulamento_id}/versoes/{versao_id}/submeter'),
}


def _enumerate_id_routes() -> set[tuple[str, str]]:
    """Todas as (metodo, path) do app com pelo menos um {param} — o denominador de SC-001."""
    found: set[tuple[str, str]] = set()
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None) or set()
        if not re.search(r"{[^}]+}", path):
            continue
        for method in methods:
            if method in ("HEAD", "OPTIONS"):
                continue
            found.add((method, path))
    return found


def test_access_classes_are_valid():
    for key, (cls, gate) in AUDIT.items():
        assert cls in ACCESS_CLASSES, f"{key}: classe invalida {cls!r}"
        assert gate and gate.strip(), f"{key}: citacao de gate vazia"


def test_every_id_route_classified():
    """SC-001 = len(classificado)/len(enumerado) == 1.0 (calculado em runtime)."""
    runtime = _enumerate_id_routes()
    audit = set(AUDIT)
    missing = runtime - audit
    extra = audit - runtime
    assert not missing, f"Rotas id-taking NAO classificadas (SC-001<100%): {sorted(missing)}"
    assert not extra, f"Entradas AUDIT que ja nao existem no app: {sorted(extra)}"
    assert len(audit & runtime) == len(runtime)
    assert runtime, "enumeracao vazia — o app nao carregou as rotas?"


def test_owner_scoped_routes_have_behavioral_coverage():
    """Toda rota owner/parent_scoped: negativo comportamental real OU citacao do gate."""
    owners = {k for k, (cls, _g) in AUDIT.items() if cls in ("owner", "parent_scoped")}
    covered = BEHAVIORAL_TESTED | BEHAVIORAL_CITED
    uncovered = owners - covered
    assert not uncovered, f"owner/parent_scoped sem prova nem citacao: {sorted(uncovered)}"
    # nao permitir cobertura orfa (rota que deixou de ser owner mas ficou citada)
    stale = covered - owners
    assert not stale, f"cobertura para rota nao-owner (rever classe/registo): {sorted(stale)}"

