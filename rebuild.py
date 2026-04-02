import re

with open('presentation.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the region between "<!-- 02" and the closing "</div>\n\n    </div>\n    <nav"
pattern = r'(        <!-- 02 배경.*?)(    </div>\n    <nav)'
match = re.search(pattern, content, re.DOTALL)
if not match:
    print("Pattern not found!")
    exit(1)

new_slides = """        <!-- 02 배경 -->
        <div class="slide surface">
            <h3>AI PoC 추진 배경</h3>
            <div class="grid" style="margin-top:3vh;">
                <div class="grid-item" style="padding:40px 28px; min-height:200px;">
                    <i class="ph ph-buildings" style="font-size:2.5rem; color:#1428A0; margin-bottom:8px;"></i>
                    <p class="name" style="color:#1428A0;">전사적 AI 활용 의지</p>
                    <p class="desc">DS부문 차원의<br>AI 도구 적극 활용 방침</p>
                </div>
                <div class="grid-item" style="padding:40px 28px; min-height:200px;">
                    <i class="ph ph-handshake" style="font-size:2.5rem; color:#1428A0; margin-bottom:8px;"></i>
                    <p class="name" style="color:#1428A0;">AI센터 협업</p>
                    <p class="desc">공통 인프라 조직과<br>메모리사업부 SW조직 협업</p>
                </div>
                <div class="grid-item" style="padding:40px 28px; min-height:200px;">
                    <i class="ph ph-rocket-launch" style="font-size:2.5rem; color:#1428A0; margin-bottom:8px;"></i>
                    <p class="name" style="color:#1428A0;">S/W개발팀 선행 수행</p>
                    <p class="desc">외부 AI 도구를 활용한<br>개발 효율화 PoC 진행</p>
                </div>
            </div>
        </div>

        <!-- 03 Claude Code -->
        <div class="slide surface">
            <h2 style="margin-bottom:1vh;">Claude Code</h2>
            <p class="sub" style="margin-bottom:3vh;">코딩 에이전트로 알려져 있지만, <span class="em">그 이상</span></p>
            <div class="grid">
                <div class="grid-item" style="padding:36px 28px; min-height:170px;">
                    <i class="ph ph-code" style="font-size:2.5rem; color:#1428A0; margin-bottom:8px;"></i>
                    <p class="name" style="color:#1428A0;">코드 작성</p>
                    <p class="desc">파일을 직접 읽고, 수정하고, 실행<br>자율적으로 판단하고 동작</p>
                </div>
                <div class="grid-item" style="padding:36px 28px; min-height:170px;">
                    <i class="ph ph-file-text" style="font-size:2.5rem; color:#1428A0; margin-bottom:8px;"></i>
                    <p class="name" style="color:#1428A0;">문서 &middot; 분석</p>
                    <p class="desc">스펙 문서 해석, 리포트 생성<br>데이터 분석 및 시각화</p>
                </div>
                <div class="grid-item" style="padding:36px 28px; min-height:170px;">
                    <i class="ph ph-desktop" style="font-size:2.5rem; color:#1428A0; margin-bottom:8px;"></i>
                    <p class="name" style="color:#1428A0;">컴퓨터 조작</p>
                    <p class="desc">터미널, 브라우저, 외부 도구<br>직접 조작하여 업무 수행</p>
                </div>
            </div>
            <div style="margin-top:3vh; max-width:1100px; width:100%; text-align:left; padding:18px 28px; background:#FFFFFF; border-left:3px solid #1428A0; box-shadow:0 2px 8px rgba(20,40,100,0.06);">
                <p style="font-size:1.05rem; color:#4A5568; line-height:1.7;">기존 챗봇은 대화형 답변 생성 &mdash; Claude Code는 파일을 직접 열고, 수정하고, 저장하는 <strong style="color:#1A1F36;">자율 에이전트</strong><br>Cursor 등 다양한 도구 비교 검토 후 성능 우위로 Claude Code 채택</p>
            </div>
        </div>

        <!-- 04 시연영상 -->
        <div class="slide surface">
            <h2 style="margin-bottom:3vh;">Claude Code 실제 동작</h2>
            <div class="img" style="max-width:800px; padding:8vh 4vw;">
                <i class="ph ph-play-circle" style="font-size:5rem; color:#D6DCE5;"></i>
                <span class="label">Demo Video</span>
                <p class="prompt">시연 영상 삽입 예정</p>
            </div>
        </div>

        <!-- 05 교육 -->
        <div class="slide surface">
            <h3>교육 &amp; 전파</h3>
            <div class="stat-grid" style="margin-top:3vh;">
                <div class="stat-card on" style="padding:40px 28px;">
                    <div class="label">PoC 교육 인원</div>
                    <div class="value">100<span style="font-size:1.5rem">명+</span></div>
                    <div class="source">2025.12 ~ 2026.03</div>
                </div>
                <div class="stat-card on" style="padding:40px 28px;">
                    <div class="label">리더진 핸즈온</div>
                    <div class="value" style="font-size:clamp(2.2rem,3.5vw,3rem);">전 임원 &middot; PL</div>
                    <div class="source">S/W개발팀 리더 전원 완료</div>
                </div>
            </div>
            <div style="margin-top:3vh; max-width:1100px; width:100%; text-align:left; padding:18px 28px; background:#FFFFFF; border-left:3px solid #1428A0; box-shadow:0 2px 8px rgba(20,40,100,0.06);">
                <p style="font-size:1.05rem; color:#4A5568; line-height:1.7;"><strong style="color:#1A1F36;">교육 내용</strong> &mdash; Claude Code 설치/사용법, 프롬프트 엔지니어링, 실제 과제 적용 실습<br><strong style="color:#1A1F36;">대상 확대</strong> &mdash; 주요 과제 PoC 인력 &rarr; 순차적으로 S/W개발팀 전 임원/PL까지 확대</p>
            </div>
        </div>

        <!-- 06 BP 사례 -->
        <div class="slide surface">
            <h3>BP 사례 &mdash; <span class="em">100건+</span></h3>
            <div class="img" style="max-width:900px; padding:6vh 4vw; margin-top:3vh;">
                <i class="ph ph-images" style="font-size:4rem; color:#D6DCE5;"></i>
                <span class="label">BP 사례 이미지</span>
                <p class="prompt">캡처 이미지 삽입 예정</p>
            </div>
            <div style="margin-top:2vh; max-width:1100px; width:100%; text-align:left; padding:18px 28px; background:#FFFFFF; border-left:3px solid #1428A0; box-shadow:0 2px 8px rgba(20,40,100,0.06);">
                <p style="font-size:1.05rem; color:#4A5568; line-height:1.7;">주요 개발 과제 중심으로 AI 활용 사례가 축적되고 있으며, 서로 공유하는 문화가 자리잡는 중</p>
            </div>
        </div>

        <!-- 07 SW Dev. Portal -->
        <div class="slide surface">
            <h3>실전 적용 &mdash; SW Dev. Portal</h3>
            <div style="display:flex; gap:20px; margin-top:2vh; width:100%; max-width:1100px; align-items:stretch;">
                <div style="flex:1; background:#EAECEF; border:1px solid #B8BCC6; border-top:3px solid #94A3B8; padding:28px 24px;">
                    <p style="font-size:0.88rem; color:#64748B; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:12px;">2022 &mdash; 프론트엔드 전환</p>
                    <p style="font-size:clamp(2.2rem,3.5vw,3.2rem); font-weight:900; color:#64748B;">10명 &middot; 1년</p>
                    <p style="font-size:1.05rem; color:#4A5568; line-height:1.8; margin-top:14px;">jQuery &rarr; Vue 전환<br>ITO 6명 별도 계약 + 혁신센터 + SE<br>매주 Sync-up 회의 진행</p>
                </div>
                <div style="flex:1; background:#E6EEFA; border:1px solid #93B4E4; border-top:3px solid #1428A0; padding:28px 24px;">
                    <p style="font-size:0.88rem; color:#1428A0; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:12px;">2026 &mdash; 백엔드 업그레이드</p>
                    <p style="font-size:clamp(2.2rem,3.5vw,3.2rem); font-weight:900; color:#1428A0;">2명 &middot; 4주</p>
                    <p style="font-size:1.05rem; color:#4A5568; line-height:1.8; margin-top:14px;">백엔드 프레임워크 전면 업그레이드<br>1,000+ 파일 &middot; 10만 Line+ 수정<br>라이브러리 의존성 전체 변경 &middot; 검증 시나리오 구성<br>전체 구조를 <strong style="color:#1428A0;">AI 친화적으로 전환 중</strong></p>
                </div>
            </div>
            <p class="sub" style="margin-top:2vh;">2022년보다 <span class="em">더 복잡한 작업</span>을 &mdash; 인원 <strong>1/5</strong>, 기간 <strong>1/12</strong></p>
        </div>

        <!-- 08 검증 -->
        <div class="slide surface">
            <h3>품질 검증 체계</h3>
            <div style="display:flex; gap:20px; margin-top:3vh; width:100%; max-width:1100px; align-items:stretch;">
                <div style="flex:1; background:#FFFFFF; border:1px solid #D6DCE5; border-top:3px solid #1428A0; padding:32px 28px; box-shadow:0 2px 8px rgba(20,40,100,0.06);">
                    <p style="font-size:1.2rem; font-weight:800; color:#1428A0; margin-bottom:16px;">공유 문화 정착</p>
                    <p style="font-size:1.05rem; color:#4A5568; line-height:1.8;">PoC 과정에서 워크플로우를 공유하고<br>서로 배우는 문화가 자리잡으면서<br>많은 어려움이 해결되고 있음</p>
                </div>
                <div style="flex:1; background:#FFFFFF; border:1px solid #D6DCE5; border-top:3px solid #1428A0; padding:32px 28px; box-shadow:0 2px 8px rgba(20,40,100,0.06);">
                    <p style="font-size:1.2rem; font-weight:800; color:#1428A0; margin-bottom:16px;">자동 검증 시스템</p>
                    <p style="font-size:clamp(2.2rem,3.5vw,3.2rem); font-weight:900; color:#1A1F36; margin:8px 0;">5,000+ <span style="font-size:1.2rem;">검증 시나리오</span></p>
                    <p style="font-size:1.05rem; color:#4A5568; line-height:1.8;">AI 활용 테스트 자동화<br>커버리지 <strong style="color:#1428A0;">90%+</strong> 확보</p>
                </div>
            </div>
            <div style="margin-top:3vh; max-width:1100px; width:100%; text-align:left; padding:18px 28px; background:#FFFFFF; border-left:3px solid #1428A0; box-shadow:0 2px 8px rgba(20,40,100,0.06);">
                <p style="font-size:1.05rem; color:#4A5568; line-height:1.7;">AI가 코드 작성 &rarr; 자동 검증 시스템이 테스트 &rarr; 사람이 최종 리뷰 &mdash; <strong style="color:#1A1F36;">AI는 도구, 책임은 엔지니어</strong></p>
            </div>
        </div>

        <!-- 09 앞으로 -->
        <div class="slide navy">
            <h1>앞으로</h1>
            <p class="sub">AI PoC <span class="em">Next Step</span></p>
            <p class="meta" style="margin-top:4vh; color:rgba(255,255,255,0.3);">PL 발표 파트</p>
        </div>

        <!-- 10 클로징 -->
        <div class="slide blue">
            <h1>감사합니다</h1>
            <p class="sub">Q &amp; A</p>
        </div>

"""

content = content[:match.start()] + new_slides + "    </div>\n    <nav" + content[match.end():]

with open('presentation.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done - 10 slides clean structure")
