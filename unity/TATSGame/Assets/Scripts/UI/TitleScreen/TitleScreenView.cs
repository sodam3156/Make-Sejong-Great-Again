using System;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.UI.TitleScreen
{
    /// <summary>
    /// TitleScreen.uxml을 그리는 UIDocument에 붙는 얇은 부트스트랩. 서버 연결 없이 뜬다
    /// (docs/23_TITLE_SCREEN_BACKLOG.md T1). 실제 씬에 이 컴포넌트를 붙이는 작업은
    /// Unity Editor가 필요해 사람이 로컬에서 한다.
    ///
    /// T7: 실제 프로세스 종료(<c>Application.Quit</c>) 호출은 이 컴포넌트가 하지 않는다 — 씬
    /// 부트스트랩이 아직 없어(README "6. 실제 server adapter 연결" 이전 단계) 종료 전 처리(예: 진행
    /// 중 로컬 저장 flush)가 필요한지 결정할 곳이 없다. <see cref="QuitRequested"/>를 받는 쪽이
    /// 이 호출을 하는 것으로 남긴다 — 사람이 씬을 연결할 때 함께 정한다.
    /// </summary>
    [RequireComponent(typeof(UIDocument))]
    public sealed class TitleScreenView : MonoBehaviour
    {
        TitleScreenPresenter _presenter;

        public event Action<TitleScreenMenuItem> MenuItemActivated;

        /// <summary>종료 확인 오버레이에서 사용자가 종료를 확정하면 발행한다.</summary>
        public event Action QuitRequested;

        void OnEnable()
        {
            var document = GetComponent<UIDocument>();
            _presenter = new TitleScreenPresenter(document.rootVisualElement);
            _presenter.MenuItemActivated += OnMenuItemActivated;
            _presenter.QuitConfirmed += OnQuitConfirmed;
        }

        void OnDisable()
        {
            if (_presenter == null)
            {
                return;
            }

            _presenter.MenuItemActivated -= OnMenuItemActivated;
            _presenter.QuitConfirmed -= OnQuitConfirmed;
            _presenter.Dispose();
            _presenter = null;
        }

        /// <summary>
        /// 서버 연결 상태를 시작 화면에 반영한다. 실제 <c>GET /api/health</c> 폴링은 T7 범위 밖이다 —
        /// <see cref="TitleScreenPresenter"/> 클래스 주석 참고. 미래의 health 어댑터가 이 메서드를 부른다.
        /// </summary>
        public void ReportConnectionStatus(TitleConnectionStatus status, string reason = null)
        {
            _presenter?.ReportConnectionStatus(status, reason);
        }

        void OnMenuItemActivated(TitleScreenMenuItem item)
        {
            MenuItemActivated?.Invoke(item);
        }

        void OnQuitConfirmed()
        {
            QuitRequested?.Invoke();
        }
    }
}
