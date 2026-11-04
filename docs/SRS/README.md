# MRPL AI Workbench — SRS

`SRS_MRPL_AI_Workbench.docx` is a Software Requirements Specification for this repository,
structured as a chapter-for-chapter analogue of a reference department SRS template
(`SRS_Transformer-Based_WAF_chapter_headings_edited.docx`): Introduction → Market Survey →
Requirements → System Architecture → Design and Implementation (DFD/ER/Class/Use
Case/Sequence) → Conclusion & Future Scope → UN SDG mapping → Appendix A (traceability).

Every requirement, table and diagram is grounded in a specific file, class, test or commit in
this repository (not written from a generic brief), and known gaps — e.g. the two independent
`Document` schemas in `backend/` vs `rag_backend/`, and the chunk-key mismatch in
`rag_backend/chat/graph.py` — are called out rather than smoothed over. See Chapter 6 and
Appendix A.

**Placeholders to fill in before submission:** mentor name, coordinator name, institute name,
and student roll numbers on the cover page — these aren't knowable from the code and were left
as bracketed placeholders.

## Regenerating

The diagrams and the four "Project Metrics" graphs (Section 3.6) are real matplotlib renders,
not hand-drawn images, so they can be regenerated if the repository's facts change (new test
counts, new contributors, etc.):

```bash
pip install matplotlib python-docx
python make_figures.py   # → figures/fig_*.png  (DFD/ER/class/use-case/sequence/context diagrams)
python make_graphs.py    # → figures/graph_*.png (test counts, commits, repo composition, format taxonomy)
python build_docx.py     # → SRS_MRPL_AI_Workbench.docx
```

`make_graphs.py` has the measured counts (test functions, commits, tracked files) hard-coded
as of 04/11/2026 — re-run the `git`/`grep` commands in Section 3.6's source captions to refresh
them before regenerating if time has passed.
