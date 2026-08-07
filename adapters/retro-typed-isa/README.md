# retro-typed-isa 기계어 검증 어댑터

Rust 제품 빌드에서 기계어를 생성하거나 옮길 때
[retro-typed-isa](https://github.com/mcpads/retro-typed-isa)를 선택할 수 있다.
Rust 참고 구현은 `expected-write`를 사용해 최종 쓰기의 원본 byte, 범위,
겹침과 미등록 diff를 확인한다.

대상 조사에서 확인한 CPU와 실행 상태에 맞는 프로필 하나만 의존 관계에
추가한다. 해당 프로필의 typed assembly 원천을 프로젝트 입력으로 두고,
조립·해석·재조립을 `MachineCodeVerifier`에 연결한다. 프로필이
`ExpectedWriteVerifier`를 제공하면 이를 사용하고, 없으면 같은 인터페이스를
구현하는 작은 프로젝트 어댑터를 둔다.

라이브러리의 프로필 검증은 명령 집합 구현의 범위를 증명한다. 프로젝트는
별도로 실제 삽입 주소, 실행 상태, 선택한 원천과 최종 `ExpectedWrite`가
일치하는지 시험한다. 기계어를 변경하지 않는 프로젝트나 다른 구현 언어에는
이 어댑터를 요구하지 않는다.
