# 레트로 게임 한글 패치 프로젝트 템플릿

배포할 권한이 없는 원본·제3자 자산을 저장소에서 제외하고, 자유로운 조사와
재현 가능한 제품 빌드를 분리하며, 위험한 이진 쓰기를 검증하기 위한
시작점이다. 플랫폼, 구현 언어, CLI와 데이터 형식은 대상 조사 뒤 프로젝트가
정한다.

한글화 판단 방법은
[create-retro-game-kr-patch](https://github.com/mcpads/create-retro-game-kr-patch)가
설명한다. 이 템플릿은 반복 빌드에서 기계적으로 막아야 할 실패 조건과
언어 중립 conformance 사례, 선택 가능한 참고 구현을 제공한다.

## 사용

새 프로젝트를 만들 때의 시작 규칙은 [`AGENTS.md`](AGENTS.md)를 따른다.
언어 중립 반례는
[`conformance/`](conformance/), Rust 참고 구현은
[`reference/rust/`](reference/rust/)에 있다.

현재 범위와 통합 상태는 [`docs/status.md`](docs/status.md), 사람의 중요한
제품 결정은 [`docs/decisions.md`](docs/decisions.md)에 두는 것이 기본값이다.
채택한 대상 명세는 [`config/`](config/), 아직 후보인 조사와 실험은
[`research/`](research/)에서 분리한다. 프로젝트에 같은 역할의 체계가 이미
있다면 그것을 유지하고 안내 경로만 바꾼다.

번역과 글꼴 자산을 채택할 때는 [`assets/translation/`](assets/translation/)과
[`assets/fonts/`](assets/fonts/)의 입력 규칙을 참고한다. 실행 검증에
emucap을 선택하면 [`adapters/emucap/`](adapters/emucap/)의 연결 규칙을
적용한다.

Rust 제품 빌드에서 기계어를 생성하거나 옮길 때 `retro-typed-isa`를
선택하면 [`adapters/retro-typed-isa/`](adapters/retro-typed-isa/)의 연결
규칙을 적용한다.

## 참고 구현 확인

```bash
cd reference/rust
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --locked
```

이 템플릿은 원격 CI 설정을 포함하지 않는다.
